"""
filters/filter_engine.py
Phase 4 -- Filter Engine

Queries the cleaned Zomato DataFrame using user preferences and returns
the top-N candidate restaurants for the LLM prompt.

Filter order (each step logs row count for debugging):
  1. Location   -- partial string match on 'location'
  2. Cuisine    -- partial string match on 'cuisines'
  3. Budget     -- cost range mapped from BUDGET_RANGES
  4. Rating     -- aggregate_rating >= min_rating
  5. Sort       -- rating DESC, votes DESC
  6. Top-N      -- return config.DEFAULT_TOP_N rows
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import BUDGET_RANGES, DEFAULT_TOP_N


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _log(step, before, after):
    """Print how many rows remain after each filter step."""
    print(f"  [Filter] {step:20s}  {before:>6,} -> {after:>6,} rows")


def _apply_location(df, location):
    if not location:
        return df
    mask = df["location"].str.contains(location, case=False, na=False, regex=False)
    return df[mask]


def _apply_cuisine(df, cuisine):
    if not cuisine:
        return df
    mask = df["cuisines"].str.contains(cuisine, case=False, na=False, regex=False)
    return df[mask]


def _apply_budget(df, budget):
    if not budget or budget not in BUDGET_RANGES:
        return df
    lo, hi = BUDGET_RANGES[budget]
    return df[(df["approx_cost"] >= lo) & (df["approx_cost"] < hi)]


def _apply_rating(df, min_rating):
    return df[df["aggregate_rating"] >= min_rating]


def _sort_and_top(df, n):
    return (
        df.sort_values(
            ["aggregate_rating", "votes"],
            ascending=[False, False]
        )
        .head(n)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Progressive relaxation (graceful degradation)
# ---------------------------------------------------------------------------

RELAXATION_STEPS = [
    # (description, field to relax)
    ("cuisine filter",     "cuisine"),
    ("budget filter",      "budget"),
    ("rating filter",      "min_rating"),
]


def _relax_and_retry(df, user_query, top_n, verbose):
    """
    If strict filtering yields no results, progressively drop filters
    one by one until we get at least some results, or give up.
    """
    query = dict(user_query)  # work on a copy

    for desc, field in RELAXATION_STEPS:
        # Relax this field
        if field == "cuisine":
            query["cuisine"] = ""
        elif field == "budget":
            query["budget"] = ""
        elif field == "min_rating":
            query["min_rating"] = 0.0

        if verbose:
            print(f"  [Relax]  Dropping {desc} and retrying ...")

        result = _run_filters(df, query, verbose=False)
        if not result.empty:
            if verbose:
                print(f"  [Relax]  Found {len(result):,} rows after dropping {desc}.")
            return _sort_and_top(result, top_n), desc  # (df, what_was_relaxed)

    return pd.DataFrame(), "all filters"  # completely empty


def _run_filters(df, query, verbose=True):
    """Apply all four filters in sequence and return the filtered DataFrame."""
    location   = query.get("location",   "")
    cuisine    = query.get("cuisine",    "")
    budget     = query.get("budget",     "")
    min_rating = query.get("min_rating", 0.0)

    result = df.copy()
    before = len(result)

    result = _apply_location(result, location)
    if verbose:
        _log("location", before, len(result)); before = len(result)

    result = _apply_cuisine(result, cuisine)
    if verbose:
        _log("cuisine", before, len(result)); before = len(result)

    result = _apply_budget(result, budget)
    if verbose:
        _log("budget", before, len(result)); before = len(result)

    result = _apply_rating(result, min_rating)
    if verbose:
        _log("rating >= " + str(min_rating), before, len(result))

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def filter_restaurants(df, user_query, top_n=None, verbose=True):
    """
    Filter the Zomato DataFrame by user preferences and return top candidates.

    Args:
        df         (pd.DataFrame): Clean dataset from load_and_preprocess().
        user_query (dict):         Validated preference dict from preference_parser.
        top_n      (int):          Max candidates to return (default: config.DEFAULT_TOP_N).
        verbose    (bool):         Log row counts at each step.

    Returns:
        dict: {
            "results"    : pd.DataFrame,   # top-N candidates (may be empty)
            "relaxed"    : str | None,     # which filter was relaxed, or None
            "count"      : int,            # number of results
            "message"    : str             # human-readable status
        }
    """
    if top_n is None:
        top_n = DEFAULT_TOP_N

    if verbose:
        print(f"\n[FilterEngine] Starting with {len(df):,} total restaurants.")
        print(f"[FilterEngine] Query: {user_query}\n")

    # ── Strict pass ──────────────────────────────────────────
    strict_result = _run_filters(df, user_query, verbose=verbose)

    if not strict_result.empty:
        top = _sort_and_top(strict_result, top_n)
        msg = f"Found {len(top)} restaurants matching all your filters."
        if verbose:
            print(f"\n[FilterEngine] {msg}")
        return {"results": top, "relaxed": None, "count": len(top), "message": msg}

    # ── Progressive relaxation ───────────────────────────────
    if verbose:
        print("\n[FilterEngine] No results with strict filters. Relaxing...")

    relaxed_df, relaxed_field = _relax_and_retry(df, user_query, top_n, verbose)

    if not relaxed_df.empty:
        msg = (f"No exact matches found. Showing {len(relaxed_df)} results "
               f"after relaxing the {relaxed_field}.")
        if verbose:
            print(f"[FilterEngine] {msg}")
        return {
            "results" : relaxed_df,
            "relaxed" : relaxed_field,
            "count"   : len(relaxed_df),
            "message" : msg
        }

    # ── Nothing at all ───────────────────────────────────────
    msg = ("No restaurants found even after relaxing all filters. "
           "Try a different location or broaden your preferences.")
    if verbose:
        print(f"[FilterEngine] {msg}")
    return {"results": pd.DataFrame(), "relaxed": "all", "count": 0, "message": msg}


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from data.dataset_loader import load_and_preprocess

    df = load_and_preprocess(verbose=False)

    # Test 1: Normal query
    print("\n" + "=" * 55)
    print("TEST 1: Normal query (Bangalore, medium, North Indian)")
    print("=" * 55)
    r = filter_restaurants(df, {
        "location"   : "bangalore",
        "budget"     : "medium",
        "cuisine"    : "north indian",
        "min_rating" : 3.5,
        "preferences": []
    })
    print(f"\nResult: {r['message']}")
    if not r["results"].empty:
        print(r["results"][["restaurant_name","location","cuisines",
                             "approx_cost","aggregate_rating","votes"]].to_string(index=False))

    # Test 2: Very restrictive (should relax)
    print("\n" + "=" * 55)
    print("TEST 2: Very restrictive (unknown cuisine + high rating)")
    print("=" * 55)
    r2 = filter_restaurants(df, {
        "location"   : "bangalore",
        "budget"     : "low",
        "cuisine"    : "martian fusion",
        "min_rating" : 4.8,
        "preferences": []
    })
    print(f"\nResult: {r2['message']}")
    if r2["relaxed"]:
        print(f"  -> Relaxed: {r2['relaxed']}")

    # Test 3: Empty location (should return no-result message)
    print("\n" + "=" * 55)
    print("TEST 3: Completely unknown location")
    print("=" * 55)
    r3 = filter_restaurants(df, {
        "location"   : "zzznowhereville",
        "budget"     : "medium",
        "cuisine"    : "",
        "min_rating" : 0.0,
        "preferences": []
    })
    print(f"\nResult: {r3['message']}")
