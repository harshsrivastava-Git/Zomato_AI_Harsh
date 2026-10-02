"""
input/preference_parser.py
Phase 3 -- User Input Layer

Collects and validates user preferences interactively (CLI),
then returns a structured query dict ready for the filter engine.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import BUDGET_RANGES, DEFAULT_MIN_RATING


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_BUDGETS = list(BUDGET_RANGES.keys())       # ["low", "medium", "high"]
RATING_MIN    = 0.0
RATING_MAX    = 5.0


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _prompt(label, default=None):
    """
    Show a prompt to the user and return stripped input.
    If the user presses Enter with no input, return `default`.
    """
    suffix = f" [{default}]" if default is not None else ""
    raw = input(f"  {label}{suffix}: ").strip()
    return raw if raw else (str(default) if default is not None else "")


def _validate_budget(value):
    """
    Return normalised budget string or None if invalid.
    Accepts: 'low', 'medium', 'high' (case-insensitive).
    """
    v = value.lower().strip()
    return v if v in VALID_BUDGETS else None


def _validate_rating(value, default):
    """
    Parse rating string -> float in [0.0, 5.0].
    Returns default on empty / invalid input.
    """
    if not value:
        return default
    try:
        r = float(value)
        if RATING_MIN <= r <= RATING_MAX:
            return round(r, 1)
        print(f"    [!] Rating must be between {RATING_MIN} and {RATING_MAX}. "
              f"Using default ({default}).")
        return default
    except ValueError:
        print(f"    [!] '{value}' is not a valid number. Using default ({default}).")
        return default


def _parse_preferences(value):
    """
    Split comma-separated extra preferences into a list.
    E.g. "family-friendly, quick service" -> ["family-friendly", "quick service"]
    Empty string -> []
    """
    if not value:
        return []
    return [p.strip().lower() for p in value.split(",") if p.strip()]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def collect_preferences():
    """
    Interactively collect and validate user restaurant preferences.

    Prompts for:
        - Location        (free-text, required)
        - Budget          (low / medium / high, required)
        - Cuisine         (free-text, optional)
        - Min Rating      (float 0.0-5.0, default: config.DEFAULT_MIN_RATING)
        - Extra Prefs     (comma-separated, optional)

    Returns:
        dict: {
            "location"    : str,
            "budget"      : str,   # "low" | "medium" | "high"
            "cuisine"     : str,
            "min_rating"  : float,
            "preferences" : list[str]
        }

    Raises:
        KeyboardInterrupt: if the user presses Ctrl+C.
    """
    print("\n" + "=" * 50)
    print("  Restaurant Preference Wizard")
    print("=" * 50)
    print("  Press Enter to accept [default] values.\n")

    # ── Location ────────────────────────────────────────────
    location = ""
    while not location:
        location = _prompt("Location (city/area)").lower().strip()
        if not location:
            print("    [!] Location is required. Please enter a city or area.")

    # ── Budget ──────────────────────────────────────────────
    budget = None
    while budget is None:
        raw = _prompt(
            f"Budget ({' / '.join(VALID_BUDGETS)})"
        )
        if not raw:
            print(f"    [!] Budget is required. Choose from: {VALID_BUDGETS}")
            continue
        budget = _validate_budget(raw)
        if budget is None:
            print(f"    [!] '{raw}' is not valid. Choose from: {VALID_BUDGETS}")

    # ── Cuisine ─────────────────────────────────────────────
    cuisine = _prompt("Cuisine type (e.g. north indian, chinese)", default="any").lower().strip()
    if cuisine == "any":
        cuisine = ""   # empty string -> no cuisine filter applied

    # ── Min Rating ──────────────────────────────────────────
    raw_rating = _prompt("Minimum rating (0.0 - 5.0)", default=DEFAULT_MIN_RATING)
    min_rating = _validate_rating(raw_rating, DEFAULT_MIN_RATING)

    # ── Extra Preferences ───────────────────────────────────
    raw_prefs = _prompt(
        "Extra preferences, comma-separated (e.g. family-friendly, rooftop)",
        default=""
    )
    preferences = _parse_preferences(raw_prefs)

    # ── Build & display structured query ────────────────────
    query = {
        "location"   : location,
        "budget"     : budget,
        "cuisine"    : cuisine,
        "min_rating" : min_rating,
        "preferences": preferences,
    }

    lo, hi = BUDGET_RANGES[budget]
    print("\n" + "-" * 50)
    print("  Your Preferences (confirmed):")
    print(f"    Location    : {query['location']}")
    print(f"    Budget      : {query['budget']}  (Rs.{lo} - Rs.{hi} for two)")
    print(f"    Cuisine     : {query['cuisine'] or 'any'}")
    print(f"    Min Rating  : {query['min_rating']}")
    print(f"    Extras      : {', '.join(query['preferences']) or 'none'}")
    print("-" * 50 + "\n")

    return query


def parse_preferences_from_dict(data: dict) -> dict:
    """
    Programmatic alternative to collect_preferences() for testing /
    pipeline use -- accepts a raw dict and validates + normalises it.

    Args:
        data (dict): Raw preference dict (may have unvalidated values).

    Returns:
        dict: Validated and normalised preference dict.

    Raises:
        ValueError: if budget or rating is invalid.
    """
    location = str(data.get("location", "")).lower().strip()
    if not location:
        raise ValueError("'location' is required and cannot be empty.")

    budget = _validate_budget(str(data.get("budget", "")))
    if budget is None:
        raise ValueError(
            f"'budget' must be one of {VALID_BUDGETS}. "
            f"Got: '{data.get('budget')}'"
        )

    cuisine = str(data.get("cuisine", "")).lower().strip()
    if cuisine == "any":
        cuisine = ""

    raw_rating = data.get("min_rating", DEFAULT_MIN_RATING)
    try:
        rating = float(raw_rating)
        if not (RATING_MIN <= rating <= RATING_MAX):
            raise ValueError(
                f"'min_rating' must be between {RATING_MIN} and {RATING_MAX}. "
                f"Got: {rating}"
            )
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid 'min_rating': {e}") from e

    preferences = _parse_preferences(str(data.get("preferences", ""))) \
        if isinstance(data.get("preferences"), str) \
        else [p.strip().lower() for p in data.get("preferences", [])]

    return {
        "location"   : location,
        "budget"     : budget,
        "cuisine"    : cuisine,
        "min_rating" : round(rating, 1),
        "preferences": preferences,
    }


# ---------------------------------------------------------------------------
# Quick test (non-interactive)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Testing parse_preferences_from_dict() ===\n")

    # Valid input
    result = parse_preferences_from_dict({
        "location"   : "Bangalore",
        "budget"     : "medium",
        "cuisine"    : "North Indian",
        "min_rating" : 3.5,
        "preferences": ["family-friendly", "quick service"]
    })
    print("Valid input result:", result)

    # Edge case: empty cuisine -> any
    result2 = parse_preferences_from_dict({
        "location": "Mumbai",
        "budget"  : "low",
        "cuisine" : "any",
        "min_rating": 0.0,
    })
    print("Empty cuisine result:", result2)

    # Edge case: invalid budget
    try:
        parse_preferences_from_dict({"location": "Delhi", "budget": "cheap"})
    except ValueError as e:
        print(f"Invalid budget caught: {e}")

    # Edge case: out-of-range rating
    try:
        parse_preferences_from_dict({"location": "Delhi", "budget": "high", "min_rating": 6.0})
    except ValueError as e:
        print(f"Out-of-range rating caught: {e}")

    print("\nAll tests passed.")
