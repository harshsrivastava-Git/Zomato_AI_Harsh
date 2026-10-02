# =============================================================
# app.py -- Main entry point (Phase 8 -- End-to-End Integration)
# =============================================================

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from data.dataset_loader        import load_and_preprocess       # Phase 2
from input.preference_parser    import collect_preferences        # Phase 3
from filters.filter_engine      import filter_restaurants         # Phase 4
from prompts.prompt_builder     import build_prompt               # Phase 5
from llm.recommendation_engine  import recommend                  # Phase 6
from output.display_formatter   import display_recommendations    # Phase 7


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_pipeline(df, user_query):
    """
    Execute the complete recommendation pipeline for one query.

    Steps:
        1. Filter dataset by user preferences
        2. Build optimised LLM prompt from candidates
        3. Call Groq LLM (fallback to rule-based on failure)
        4. Display formatted recommendation cards
    """

    # ── Step 1: Filter ────────────────────────────────────────
    print("\n[Step 1/3]  Filtering restaurants...")
    filter_result = filter_restaurants(df, user_query, verbose=True)
    candidates    = filter_result["results"]

    if candidates.empty:
        print(f"\n  No restaurants found: {filter_result['message']}")
        print("  Try broadening your location or relaxing the cuisine / budget filter.")
        return

    # ── Step 2: Build prompt + call LLM ───────────────────────
    print("\n[Step 2/3]  Building prompt & calling Groq LLM...")
    prompt = build_prompt(user_query, candidates)
    output = recommend(prompt, candidates)

    # ── Step 3: Display ────────────────────────────────────────
    print("\n[Step 3/3]  Formatting results...")
    display_recommendations(
        recommendations = output["recommendations"],
        original_df     = df,
        source          = output["source"],
        user_query      = user_query,
        output_mode     = "terminal",
    )

    if output.get("error"):
        print(f"  [Note] LLM error (fallback was used): {output['error']}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print()
    print("=" * 64)
    print("   ZOMATO AI RESTAURANT RECOMMENDER")
    print("   Powered by Groq LLM  |  51,000+ restaurants")
    print("=" * 64)

    # Load dataset once
    print("\nLoading dataset (first run may take a moment)...")
    df = load_and_preprocess(verbose=True)

    # Interactive loop — keep asking until user quits
    while True:
        print()
        print("-" * 64)
        print("  Enter your preferences  (type 'quit' at Location to exit)")
        print("-" * 64)

        try:
            user_query = collect_preferences()          # Phase 3 interactive CLI

            # Allow quit typed as the location value
            if user_query.get("location", "").strip().lower() in ("quit", "exit", "q"):
                print("\nGoodbye!")
                break

        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!")
            break

        run_pipeline(df, user_query)

        # Ask if user wants another search
        print()
        try:
            again = input("  Search again? (y/n): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            again = "n"

        if again not in ("y", "yes"):
            print("\nThank you for using Zomato AI Recommender! Goodbye.")
            break


if __name__ == "__main__":
    main()
