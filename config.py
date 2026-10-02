# =============================================================
# config.py -- Centralized configuration for the recommender
# =============================================================

import os
from dotenv import load_dotenv

load_dotenv()

# -- LLM Settings (Groq) ------------------------------------------------------
LLM_PROVIDER = "groq"

# Active Groq models (verified 2026-10):
#   qwen/qwen3.8-27b      -- fast, capable (default)
#   openai/gpt-oss-20b    -- alternative
GROQ_MODEL   = "qwen/qwen3.8-27b"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# -- Dataset ------------------------------------------------------------------
DATASET_ID    = "ManikaSaini/zomato-restaurant-recommendation"
DATASET_SPLIT = "train"
CLEAN_CSV     = "data/zomato_clean.csv"

# -- Filter Defaults ----------------------------------------------------------
DEFAULT_MIN_RATING = 3.0
DEFAULT_TOP_N      = 12     # candidate rows sent to LLM prompt

# -- Budget Range Mappings (approx cost for two, in INR) ----------------------
BUDGET_RANGES = {
    "low":    (0,   400),
    "medium": (400, 800),
    "high":   (800, 9999),
}

# -- Output -------------------------------------------------------------------
TOP_RECOMMENDATIONS = 5    # how many the LLM picks from candidates

# -- Prompt token safety ------------------------------------------------------
MAX_PROMPT_RESTAURANTS = 15   # hard cap: trim list if > this many rows
