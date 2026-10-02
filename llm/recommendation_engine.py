"""
llm/recommendation_engine.py
Phase 6 -- LLM Integration (Groq)

Sends the engineered prompt to Groq and parses the structured response.
Falls back to rule-based top-N if the LLM call fails.
"""

import os
import sys
import time
import re
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import GROQ_API_KEY, GROQ_MODEL, TOP_RECOMMENDATIONS
from prompts.prompt_builder import get_messages

# ---------------------------------------------------------------------------
# Groq client setup
# ---------------------------------------------------------------------------

try:
    from groq import Groq
    _groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except ImportError:
    _groq_client = None
    print("[WARNING] groq package not installed. Run: pip install groq")


# ---------------------------------------------------------------------------
# LLM call with retry + backoff
# ---------------------------------------------------------------------------

def get_recommendations(prompt_dict, max_retries=3, backoff_base=2):
    """
    Send the engineered prompt to Groq and return the raw text response.

    Args:
        prompt_dict  (dict): Output of build_prompt() -- {system, user, n_items}.
        max_retries  (int):  Number of retry attempts on transient errors.
        backoff_base (int):  Base seconds for exponential backoff.

    Returns:
        dict: {
            "raw_text"  : str,   # LLM response text (or None on failure)
            "source"    : str,   # "llm" | "fallback"
            "model"     : str,
            "error"     : str | None
        }
    """
    if _groq_client is None:
        return {
            "raw_text": None,
            "source"  : "fallback",
            "model"   : "none",
            "error"   : "Groq client unavailable. Check GROQ_API_KEY and groq package."
        }

    messages = get_messages(prompt_dict)
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[LLM] Calling Groq ({GROQ_MODEL}) — attempt {attempt}/{max_retries} ...")
            response = _groq_client.chat.completions.create(
                model      = GROQ_MODEL,
                messages   = messages,
                temperature= 0.7,
                max_tokens = 1024,
            )
            raw_text = response.choices[0].message.content.strip()

            if not raw_text:
                raise ValueError("Empty response received from Groq.")

            print(f"[LLM] Response received ({len(raw_text)} chars).")
            return {
                "raw_text": raw_text,
                "source"  : "llm",
                "model"   : GROQ_MODEL,
                "error"   : None
            }

        except Exception as e:
            last_error = str(e)
            wait = backoff_base ** attempt
            print(f"[LLM] Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(f"[LLM] Retrying in {wait}s ...")
                time.sleep(wait)

    print(f"[LLM] All {max_retries} attempts failed. Switching to fallback.")
    return {
        "raw_text": None,
        "source"  : "fallback",
        "model"   : GROQ_MODEL,
        "error"   : last_error
    }


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

def parse_response(raw_text):
    """
    Parse the LLM's numbered-list response into structured recommendation dicts.

    Handles labelled lines like:
        1. Restaurant Name
           Explanation: ...
           Caveat: ...

    Args:
        raw_text (str): Raw LLM response string.

    Returns:
        list[dict]: [
            {
                "rank"       : int,
                "name"       : str,
                "explanation": str,
                "caveat"     : str
            },
            ...
        ]
    """
    if not raw_text:
        return []

    recommendations = []

    # Keyword prefixes that signal explanation vs caveat sections
    EXPLANATION_KEYS = ("explanation:", "why it fits:", "reason:", "description:",
                        "why:", "about:", "why this restaurant:")
    CAVEAT_KEYS      = ("caveat:", "note:", "caveats:", "things to note:",
                        "be aware:", "downside:", "however,", "watch out:")

    # Split on numbered list markers: "1.", "2.", etc.
    blocks = re.split(r"\n(?=\d+[\.\)])", raw_text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Extract rank number
        rank_match = re.match(r"^(\d+)[.\)]\s*", block)
        if not rank_match:
            continue
        rank = int(rank_match.group(1))
        rest_of_block = block[rank_match.end():].strip()

        lines = [l.strip() for l in rest_of_block.split("\n") if l.strip()]
        if not lines:
            continue

        # First line = restaurant name (strip markdown bold/italic)
        name = re.sub(r"[*_#]", "", lines[0]).strip(":- ")

        # Parse remaining lines into explanation / caveat buckets
        explanation_parts = []
        caveat_parts      = []
        current_bucket    = "explanation"   # default: collect into explanation

        for line in lines[1:]:
            line_low = line.lower().strip()

            # Check if this line starts a new labelled section
            if any(line_low.startswith(k) for k in CAVEAT_KEYS):
                current_bucket = "caveat"
                # Strip the keyword prefix from the line itself
                for k in CAVEAT_KEYS:
                    if line_low.startswith(k):
                        line = line[len(k):].strip("*_ ")
                        break
            elif any(line_low.startswith(k) for k in EXPLANATION_KEYS):
                current_bucket = "explanation"
                for k in EXPLANATION_KEYS:
                    if line_low.startswith(k):
                        line = line[len(k):].strip("*_ ")
                        break

            clean = re.sub(r"[*_]", "", line).strip()
            if not clean:
                continue

            if current_bucket == "caveat":
                caveat_parts.append(clean)
            else:
                explanation_parts.append(clean)

        explanation = " ".join(explanation_parts).strip() or "See restaurant details above."
        caveat      = " ".join(caveat_parts).strip()      or "None noted."

        recommendations.append({
            "rank"       : rank,
            "name"       : name,
            "explanation": explanation,
            "caveat"     : caveat,
        })

    return recommendations


# ---------------------------------------------------------------------------
# Rule-based fallback
# ---------------------------------------------------------------------------

def fallback_recommendations(candidates_df, top_n=None):
    """
    When LLM is unavailable, return top-N by rating then votes as structured dicts.

    Args:
        candidates_df (pd.DataFrame): Filter engine output.
        top_n         (int):          How many to return.

    Returns:
        list[dict]: Same schema as parse_response() output.
    """
    if top_n is None:
        top_n = TOP_RECOMMENDATIONS

    if candidates_df is None or candidates_df.empty:
        return []

    top = (
        candidates_df
        .sort_values(["aggregate_rating", "votes"], ascending=[False, False])
        .drop_duplicates(subset=["restaurant_name"])
        .head(top_n)
        .reset_index(drop=True)
    )

    results = []
    for i, row in top.iterrows():
        name   = str(row.get("restaurant_name", "Unknown")).title()
        rating = row.get("aggregate_rating", 0.0)
        cost   = row.get("approx_cost", 0)
        votes  = row.get("votes", 0)

        results.append({
            "rank"       : i + 1,
            "name"       : name,
            "explanation": (
                f"Rated {rating}/5 with {votes:,} votes. "
                f"Approximate cost is Rs.{cost} for two. "
                f"Selected by rule-based ranking (LLM unavailable)."
            ),
            "caveat"     : "Recommendation generated without AI — LLM was unavailable.",
        })

    return results


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def recommend(prompt_dict, candidates_df):
    """
    Full recommendation pipeline:
      1. Call Groq LLM
      2. Parse the response
      3. If LLM fails or returns nothing parseable, use rule-based fallback

    Args:
        prompt_dict   (dict):         build_prompt() output.
        candidates_df (pd.DataFrame): filter_restaurants() results DataFrame.

    Returns:
        dict: {
            "recommendations": list[dict],   # [{rank, name, explanation, caveat}]
            "source"         : str,          # "llm" | "fallback"
            "raw_text"       : str | None,
            "error"          : str | None
        }
    """
    llm_result = get_recommendations(prompt_dict)

    if llm_result["source"] == "llm" and llm_result["raw_text"]:
        parsed = parse_response(llm_result["raw_text"])
        if parsed:
            return {
                "recommendations": parsed,
                "source"         : "llm",
                "raw_text"       : llm_result["raw_text"],
                "error"          : None
            }
        print("[LLM] Parsing returned no results. Using rule-based fallback.")

    # Fallback
    fb = fallback_recommendations(candidates_df)
    return {
        "recommendations": fb,
        "source"         : "fallback",
        "raw_text"       : llm_result.get("raw_text"),
        "error"          : llm_result.get("error")
    }


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from data.dataset_loader   import load_and_preprocess
    from filters.filter_engine import filter_restaurants
    from prompts.prompt_builder import build_prompt

    df = load_and_preprocess(verbose=False)
    result = filter_restaurants(df, {
        "location"   : "bangalore",
        "budget"     : "medium",
        "cuisine"    : "north indian",
        "min_rating" : 3.5,
        "preferences": ["family-friendly"],
    }, verbose=False)

    candidates = result["results"]
    prompt     = build_prompt(
        {"location":"bangalore","budget":"medium","cuisine":"north indian",
         "min_rating":3.5,"preferences":["family-friendly"]},
        candidates
    )

    print("=" * 60)
    print("TEST 1: Full LLM pipeline (needs GROQ_API_KEY in .env)")
    print("=" * 60)
    output = recommend(prompt, candidates)
    print(f"\nSource : {output['source']}")
    print(f"Error  : {output['error']}")
    print(f"\nRecommendations ({len(output['recommendations'])}):")
    for r in output["recommendations"]:
        print(f"\n  [{r['rank']}] {r['name']}")
        print(f"      Explanation : {r['explanation']}")
        print(f"      Caveat      : {r['caveat']}")

    print("\n" + "=" * 60)
    print("TEST 2: Rule-based fallback directly")
    print("=" * 60)
    fb = fallback_recommendations(candidates, top_n=3)
    for r in fb:
        print(f"  [{r['rank']}] {r['name']} — {r['explanation'][:80]}...")
