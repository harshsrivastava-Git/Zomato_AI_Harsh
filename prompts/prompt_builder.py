"""
prompts/prompt_builder.py
Phase 5 -- Prompt Engineering

Transforms filtered restaurant candidates + user preferences into
an optimised, token-safe prompt ready for the Groq LLM API.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import BUDGET_RANGES, TOP_RECOMMENDATIONS, MAX_PROMPT_RESTAURANTS


# ---------------------------------------------------------------------------
# System prompt (role definition)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a restaurant recommendation expert helping a user find "
    "the perfect restaurant in India. "
    "Be concise, friendly, and helpful. "
    "Only recommend restaurants from the list provided to you."
)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_restaurant_line(row):
    """
    Convert one DataFrame row into a single readable line for the prompt.
    Example output:
      - Name: Spice Garden | Cuisine: north indian | Rating: 4.3 | Cost: Rs.450 | Votes: 1200
    """
    name    = str(row.get("restaurant_name", "Unknown")).title()
    cuisine = str(row.get("cuisines", "N/A")).title()
    rating  = row.get("aggregate_rating", 0.0)
    cost    = row.get("approx_cost", 0)
    votes   = row.get("votes", 0)
    online  = row.get("online_order", "N/A")
    book    = row.get("book_table",   "N/A")

    line = (
        f"- Name: {name} | "
        f"Cuisine: {cuisine} | "
        f"Rating: {rating}/5 | "
        f"Cost: Rs.{cost} for two | "
        f"Votes: {votes}"
    )

    # Append convenience flags only if data is available
    extras = []
    if str(online).strip().lower() == "yes":
        extras.append("Online Order: Yes")
    if str(book).strip().lower() == "yes":
        extras.append("Table Booking: Yes")
    if extras:
        line += " | " + " | ".join(extras)

    return line


def _build_restaurant_list(candidates_df, max_rows):
    """
    Format the candidates DataFrame into a prompt-safe text block.
    Trims to `max_rows` if needed to stay within token limits.
    """
    df = candidates_df.head(max_rows)
    lines = [_format_restaurant_line(row) for _, row in df.iterrows()]
    return "\n".join(lines)


def _format_preferences(query):
    """Turn the preferences list into a human-readable string."""
    prefs = query.get("preferences", [])
    return ", ".join(prefs) if prefs else "none specified"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_prompt(user_query, candidates_df, max_restaurants=None):
    """
    Build the full LLM prompt from user preferences + filtered candidates.

    Args:
        user_query      (dict):         Validated preference dict from Phase 3.
        candidates_df   (pd.DataFrame): Top candidates from Phase 4 filter engine.
        max_restaurants (int):          Hard cap on restaurants in prompt.
                                        Defaults to config.MAX_PROMPT_RESTAURANTS.

    Returns:
        dict: {
            "system"  : str,   # system role message
            "user"    : str,   # user turn message (the main prompt)
            "n_items" : int    # number of restaurants included
        }

    Raises:
        ValueError: if candidates_df is empty.
    """
    if max_restaurants is None:
        max_restaurants = MAX_PROMPT_RESTAURANTS

    if candidates_df is None or candidates_df.empty:
        raise ValueError(
            "candidates_df is empty. Run filter_restaurants() first."
        )

    # ── Extract query fields ─────────────────────────────────
    location   = user_query.get("location",    "any").title()
    budget     = user_query.get("budget",      "any")
    cuisine    = user_query.get("cuisine",     "") or "any"
    min_rating = user_query.get("min_rating",  3.0)
    preferences = _format_preferences(user_query)

    lo, hi = BUDGET_RANGES.get(budget, (0, 9999))
    budget_label = f"{budget.capitalize()} (approx Rs.{lo}-Rs.{hi} for two)"

    # ── Build restaurant list block ──────────────────────────
    n_items = min(len(candidates_df), max_restaurants)
    restaurant_list = _build_restaurant_list(candidates_df, n_items)

    # ── Compose user prompt ──────────────────────────────────
    user_prompt = f"""User Preferences:
- Location  : {location}
- Budget    : {budget_label}
- Cuisine   : {cuisine}
- Min Rating: {min_rating} / 5.0
- Special   : {preferences}

Available Restaurants (pre-filtered, sorted by rating then votes):
{restaurant_list}

Task:
From the list above, recommend the top {TOP_RECOMMENDATIONS} restaurants that best fit this user.
For each recommendation provide:
1. Restaurant name (exactly as listed above)
2. A 2-3 sentence explanation of why it suits this user's preferences
3. Any caveats or things to be aware of (e.g. no table booking, limited cuisine variety)

Format your response as a numbered list. Do not recommend restaurants not in the list above."""

    return {
        "system" : SYSTEM_PROMPT,
        "user"   : user_prompt,
        "n_items": n_items,
    }


def get_messages(prompt_dict):
    """
    Convert the prompt dict into the Groq/OpenAI messages list format.

    Args:
        prompt_dict (dict): Output of build_prompt().

    Returns:
        list[dict]: [{"role": "system", ...}, {"role": "user", ...}]
    """
    return [
        {"role": "system", "content": prompt_dict["system"]},
        {"role": "user",   "content": prompt_dict["user"]},
    ]


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from data.dataset_loader    import load_and_preprocess
    from filters.filter_engine  import filter_restaurants

    # Load + filter
    df = load_and_preprocess(verbose=False)
    result = filter_restaurants(df, {
        "location"   : "bangalore",
        "budget"     : "medium",
        "cuisine"    : "north indian",
        "min_rating" : 3.5,
        "preferences": ["family-friendly"],
    }, verbose=False)

    candidates = result["results"]
    print(f"Candidates passed to prompt builder: {len(candidates)}")

    # Build prompt
    prompt = build_prompt(
        user_query={
            "location"   : "bangalore",
            "budget"     : "medium",
            "cuisine"    : "north indian",
            "min_rating" : 3.5,
            "preferences": ["family-friendly"],
        },
        candidates_df=candidates,
    )

    print(f"\nRestaurants in prompt : {prompt['n_items']}")
    print("\n" + "=" * 60)
    print("SYSTEM PROMPT:")
    print("=" * 60)
    print(prompt["system"])
    print("\n" + "=" * 60)
    print("USER PROMPT:")
    print("=" * 60)
    print(prompt["user"])
    print("\n" + "=" * 60)
    print("MESSAGES FORMAT (for Groq API):")
    print("=" * 60)
    messages = get_messages(prompt)
    for m in messages:
        print(f"  role={m['role']!r}  content_length={len(m['content'])} chars")

    # Edge case: empty candidates
    print("\n--- Edge case: empty DataFrame ---")
    try:
        build_prompt({"location": "delhi", "budget": "low"}, pd.DataFrame())
    except ValueError as e:
        print(f"Caught expected error: {e}")
