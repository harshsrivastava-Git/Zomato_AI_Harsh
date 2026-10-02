"""
output/display_formatter.py
Phase 7 -- Output Display Layer

Formats and prints final restaurant recommendations as styled
terminal cards. Also supports JSON output mode for API/pipeline use.
"""

import os
import sys
import json
import textwrap
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import BUDGET_RANGES

# ---------------------------------------------------------------------------
# Card layout constants
# ---------------------------------------------------------------------------
CARD_WIDTH    = 62   # total inner width (between borders)
BORDER_TOP    = "+" + "-" * CARD_WIDTH + "+"
BORDER_BOT    = "+" + "-" * CARD_WIDTH + "+"
RANK_ICONS    = {1: "[ #1 ]", 2: "[ #2 ]", 3: "[ #3 ]", 4: "[ #4 ]", 5: "[ #5 ]"}
SOURCE_LABELS = {"llm": "AI-Powered", "fallback": "Rule-Based"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row(text, pad=" "):
    """Format one line inside the card, left-padded, right-padded to CARD_WIDTH."""
    inner = f"  {text}"
    if len(inner) > CARD_WIDTH:
        inner = inner[:CARD_WIDTH - 1]
    return f"|{inner:<{CARD_WIDTH}}|"


def _wrapped_rows(label, text, indent=18):
    """
    Wrap long text (e.g. AI explanation) across multiple card rows.
    First line shows the label; subsequent lines are indented to align.
    """
    max_first  = CARD_WIDTH - len(f"  {label}")
    max_cont   = CARD_WIDTH - indent - 2

    words      = text.split()
    lines      = []
    current    = ""

    for word in words:
        max_len = max_first if not lines else max_cont
        if len(current) + len(word) + (1 if current else 0) <= max_len:
            current = (current + " " + word).strip()
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    rows = []
    for i, line in enumerate(lines):
        if i == 0:
            rows.append(_row(f"{label}{line}"))
        else:
            rows.append(_row(f"{' ' * (indent - 2)}{line}"))
    return rows


def _enrich(name, original_df):
    """
    Look up a restaurant name in the original DataFrame to get
    real rating, cost, cuisine, votes, online_order, book_table.
    Returns first match or a dict of defaults.
    """
    if original_df is None or original_df.empty:
        return {}

    match = original_df[
        original_df["restaurant_name"].str.lower() == name.lower()
    ]

    if match.empty:
        # Try partial match
        match = original_df[
            original_df["restaurant_name"].str.contains(name.lower(),
                                                         case=False, na=False)
        ]

    if match.empty:
        return {}

    row = match.sort_values("aggregate_rating", ascending=False).iloc[0]
    return row.to_dict()


def _format_budget_label(budget):
    """e.g. 'medium' -> 'Medium (Rs.400-800)'"""
    if budget in BUDGET_RANGES:
        lo, hi = BUDGET_RANGES[budget]
        return f"{budget.capitalize()} (Rs.{lo}-{hi})"
    return budget.capitalize() if budget else "Any"


# ---------------------------------------------------------------------------
# Single card renderer
# ---------------------------------------------------------------------------

def _render_card(rec, data, rank_label):
    """
    Render one recommendation as a bordered ASCII card.

    Args:
        rec        (dict): {rank, name, explanation, caveat}
        data       (dict): Enriched dataset fields for this restaurant
        rank_label (str):  e.g. "[ #1 ]"

    Returns:
        list[str]: Lines of the card (print each with print())
    """
    name     = rec.get("name",  "Unknown")
    expl     = rec.get("explanation", "")
    caveat   = rec.get("caveat", "None noted.")
    rating   = data.get("aggregate_rating", "N/A")
    cost     = data.get("approx_cost", "N/A")
    votes    = data.get("votes", "N/A")
    cuisines = data.get("cuisines", "N/A")
    online   = data.get("online_order", "N/A")
    book     = data.get("book_table",   "N/A")

    # Format votes
    votes_str = f"{int(votes):,}" if str(votes).isdigit() or isinstance(votes, (int, float)) else str(votes)

    card = [BORDER_TOP]

    # Title row
    title = f"{rank_label}  {name.title()}"
    card.append(_row(title))
    card.append(_row("-" * (CARD_WIDTH - 4)))

    # Dataset fields
    card.append(_row(f"Cuisine  :  {str(cuisines).title()[:40]}"))
    card.append(_row(f"Rating   :  {rating} / 5   ({votes_str} votes)"))
    card.append(_row(f"Cost     :  Rs.{cost} for two"))

    # Convenience flags
    flags = []
    if str(online).strip().lower() == "yes":
        flags.append("Online Order")
    if str(book).strip().lower() == "yes":
        flags.append("Table Booking")
    if flags:
        card.append(_row(f"Features :  {' | '.join(flags)}"))

    card.append(_row("-" * (CARD_WIDTH - 4)))

    # AI explanation (wrapped)
    if expl and expl != "See restaurant details above.":
        card += _wrapped_rows("AI Note  :  \"", expl, indent=14)
        card.append(_row("             \""))
    else:
        card.append(_row("AI Note  :  See dataset fields above."))

    # Caveat (only if meaningful)
    if caveat and caveat.lower() not in ("none noted.", "none.", "n/a", ""):
        card += _wrapped_rows("Caveat   :  ", caveat, indent=14)

    card.append(BORDER_BOT)
    return card


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def display_recommendations(recommendations, original_df=None,
                             source="llm", user_query=None,
                             output_mode="terminal"):
    """
    Format and display restaurant recommendations.

    Args:
        recommendations (list[dict]):  [{rank, name, explanation, caveat}]
        original_df     (pd.DataFrame): Full clean dataset for enrichment.
        source          (str):          "llm" | "fallback"
        user_query      (dict):         User preferences (for summary line).
        output_mode     (str):          "terminal" (print) | "json" (return dict)

    Returns:
        If output_mode == "json": returns a dict with all formatted data.
        Otherwise: prints to terminal and returns None.
    """
    if not recommendations:
        msg = "No recommendations to display."
        if output_mode == "json":
            return {"error": msg, "recommendations": []}
        print(f"\n  {msg}\n")
        return

    source_label = SOURCE_LABELS.get(source, source.upper())

    if output_mode == "terminal":
        _print_header(user_query, source_label, len(recommendations))

    cards_data = []
    for rec in recommendations:
        rank   = rec.get("rank", 0)
        name   = rec.get("name", "Unknown")
        data   = _enrich(name, original_df)
        label  = RANK_ICONS.get(rank, f"[ #{rank} ]")
        lines  = _render_card(rec, data, label)
        cards_data.append({"rec": rec, "data": data, "lines": lines})

        if output_mode == "terminal":
            print()
            for line in lines:
                print(line)

    if output_mode == "terminal":
        _print_summary(recommendations, cards_data, user_query, source_label)
        return None

    # JSON mode — return structured data
    return {
        "source"         : source,
        "query"          : user_query,
        "count"          : len(recommendations),
        "recommendations": [
            {
                "rank"           : r["rec"]["rank"],
                "name"           : r["rec"]["name"],
                "explanation"    : r["rec"]["explanation"],
                "caveat"         : r["rec"]["caveat"],
                "aggregate_rating": r["data"].get("aggregate_rating", None),
                "approx_cost"    : r["data"].get("approx_cost", None),
                "cuisines"       : r["data"].get("cuisines", None),
                "votes"          : r["data"].get("votes", None),
                "online_order"   : r["data"].get("online_order", None),
                "book_table"     : r["data"].get("book_table", None),
            }
            for r in cards_data
        ]
    }


def _print_header(user_query, source_label, count):
    """Print the banner above the recommendation cards."""
    print()
    print("=" * (CARD_WIDTH + 2))
    print(f"  ZOMATO AI RESTAURANT RECOMMENDER  [{source_label}]")
    print("=" * (CARD_WIDTH + 2))

    if user_query:
        loc     = user_query.get("location", "any").title()
        budget  = _format_budget_label(user_query.get("budget", ""))
        cuisine = user_query.get("cuisine", "") or "Any"
        rating  = user_query.get("min_rating", 3.0)
        print(f"  Location : {loc}")
        print(f"  Budget   : {budget}")
        print(f"  Cuisine  : {cuisine.title()}")
        print(f"  Min Rtg  : {rating}")
    print(f"  Results  : {count} recommendations")
    print("-" * (CARD_WIDTH + 2))


def _print_summary(recommendations, cards_data, user_query, source_label):
    """Print a one-line summary after all cards."""
    print()
    print("=" * (CARD_WIDTH + 2))
    print("  TOP PICK SUMMARY")
    print("=" * (CARD_WIDTH + 2))

    for cd in cards_data:
        rank    = cd["rec"]["rank"]
        name    = cd["rec"]["name"].title()
        rating  = cd["data"].get("aggregate_rating", "N/A")
        cost    = cd["data"].get("approx_cost", "N/A")
        print(f"  #{rank}  {name:<28}  Rating: {rating}/5   Cost: Rs.{cost}")

    top_name = recommendations[0].get("name", "N/A").title()
    print()
    print(f"  Our top pick: {top_name}")
    print(f"  Powered by  : {source_label}")
    print("=" * (CARD_WIDTH + 2))
    print()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from data.dataset_loader      import load_and_preprocess
    from filters.filter_engine    import filter_restaurants
    from prompts.prompt_builder   import build_prompt
    from llm.recommendation_engine import recommend

    df = load_and_preprocess(verbose=False)
    query = {
        "location"   : "bangalore",
        "budget"     : "medium",
        "cuisine"    : "north indian",
        "min_rating" : 3.5,
        "preferences": ["family-friendly"],
    }

    result     = filter_restaurants(df, query, verbose=False)
    candidates = result["results"]
    prompt     = build_prompt(query, candidates)
    output     = recommend(prompt, candidates)

    print("\n--- TERMINAL MODE ---")
    display_recommendations(
        recommendations = output["recommendations"],
        original_df     = df,
        source          = output["source"],
        user_query      = query,
        output_mode     = "terminal",
    )

    print("\n--- JSON MODE (first item) ---")
    json_out = display_recommendations(
        recommendations = output["recommendations"],
        original_df     = df,
        source          = output["source"],
        user_query      = query,
        output_mode     = "json",
    )
    print(json.dumps(json_out["recommendations"][0], indent=2))
