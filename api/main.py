"""
api/main.py
Phase 10 -- REST API Layer

Exposes the full recommendation pipeline as a FastAPI HTTP service.

Endpoints:
  GET  /           -- API info
  GET  /health     -- liveness check
  GET  /locations  -- unique locations in dataset
  GET  /cuisines   -- unique cuisines in dataset
  POST /recommend  -- full pipeline: filter -> prompt -> LLM -> response

Run with:
  uvicorn api.main:app --reload --port 8000
  (from the zomato-ai-recommender/ directory)
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import BUDGET_RANGES, DEFAULT_MIN_RATING, GROQ_MODEL
from data.dataset_loader      import load_and_preprocess
from filters.filter_engine    import filter_restaurants
from prompts.prompt_builder   import build_prompt
from llm.recommendation_engine import recommend

import pandas as pd

# ---------------------------------------------------------------------------
# Global state (dataset loaded once at startup)
# ---------------------------------------------------------------------------
_state: dict = {"df": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load dataset at startup; release on shutdown."""
    print("[Startup] Loading Zomato dataset...")
    _state["df"] = load_and_preprocess(verbose=False)
    print(f"[Startup] Dataset ready: {len(_state['df']):,} restaurants.")
    yield
    print("[Shutdown] Cleaning up.")
    _state["df"] = None


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title       = "Zomato AI Restaurant Recommender",
    description = (
        "AI-powered restaurant recommendation API using Groq LLM. "
        "Filter restaurants by location, budget, cuisine and rating, "
        "then get intelligent recommendations with explanations."
    ),
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
VALID_BUDGETS = list(BUDGET_RANGES.keys())

class PreferenceRequest(BaseModel):
    location   : str                  = Field(..., example="bangalore", description="City or area to search in")
    budget     : str                  = Field(..., example="medium",    description="low | medium | high")
    cuisine    : Optional[str]        = Field("",  example="north indian", description="Cuisine type (leave empty for any)")
    min_rating : Optional[float]      = Field(DEFAULT_MIN_RATING, ge=0.0, le=5.0, description="Minimum aggregate rating (0-5)")
    preferences: Optional[list[str]]  = Field([], example=["family-friendly", "quick service"], description="Extra preference tags")

    @validator("budget")
    def validate_budget(cls, v):
        if v.lower() not in VALID_BUDGETS:
            raise ValueError(f"budget must be one of {VALID_BUDGETS}")
        return v.lower()

    @validator("location")
    def validate_location(cls, v):
        if not v.strip():
            raise ValueError("location cannot be empty")
        return v.strip().lower()


class RecommendationItem(BaseModel):
    rank             : int
    name             : str
    explanation      : str
    caveat           : str
    aggregate_rating : Optional[float] = None
    approx_cost      : Optional[int]   = None
    cuisines         : Optional[str]   = None
    votes            : Optional[int]   = None
    online_order     : Optional[str]   = None
    book_table       : Optional[str]   = None


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationItem]
    source         : str    # "llm" | "fallback"
    filter_message : str
    count          : int
    model_used     : str
    error          : Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Info"])
def root():
    """API information and available endpoints."""
    return {
        "name"     : "Zomato AI Restaurant Recommender",
        "version"  : "1.0.0",
        "model"    : GROQ_MODEL,
        "endpoints": {
            "GET  /"          : "This info page",
            "GET  /health"    : "Liveness check",
            "GET  /locations" : "List unique locations in dataset",
            "GET  /cuisines"  : "List unique cuisines in dataset",
            "POST /recommend" : "Get AI-powered restaurant recommendations",
            "GET  /docs"      : "Swagger UI (interactive API docs)",
        }
    }


@app.get("/health", tags=["Info"])
def health():
    """Liveness check — returns OK if dataset is loaded."""
    df = _state.get("df")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Dataset not loaded yet.")
    return {
        "status"            : "ok",
        "dataset_rows"      : len(df),
        "model"             : GROQ_MODEL,
    }


@app.get("/locations", tags=["Discovery"])
def get_locations(limit: int = 100):
    """
    Return a sorted list of unique locations available in the dataset.
    Useful for populating dropdowns in a frontend UI.
    """
    df = _state.get("df")
    if df is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded.")

    locations = (
        df["location"]
        .dropna()
        .str.strip()
        .unique()
        .tolist()
    )
    locations = sorted(set(l for l in locations if l))[:limit]
    return {"locations": locations, "count": len(locations)}


@app.get("/cuisines", tags=["Discovery"])
def get_cuisines(limit: int = 100):
    """
    Return a sorted list of unique cuisine types in the dataset.
    Useful for populating dropdowns in a frontend UI.
    """
    df = _state.get("df")
    if df is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded.")

    all_cuisines = set()
    for cell in df["cuisines"].dropna():
        for c in str(cell).split(","):
            c = c.strip().lower()
            if c:
                all_cuisines.add(c)

    cuisines = sorted(all_cuisines)[:limit]
    return {"cuisines": cuisines, "count": len(cuisines)}


@app.post("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
def recommend_restaurants(request: PreferenceRequest):
    """
    Full recommendation pipeline:
      1. Validate & normalize user preferences
      2. Filter dataset by location / cuisine / budget / rating
      3. Build optimized LLM prompt
      4. Call Groq LLM (with fallback to rule-based if LLM fails)
      5. Return structured recommendations with explanations

    Returns top 5 restaurant recommendations with AI-generated explanations.
    """
    df = _state.get("df")
    if df is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded.")

    user_query = {
        "location"   : request.location,
        "budget"     : request.budget,
        "cuisine"    : request.cuisine or "",
        "min_rating" : request.min_rating,
        "preferences": request.preferences or [],
    }

    # Step 1: Filter
    filter_result = filter_restaurants(df, user_query, verbose=False)
    candidates    = filter_result["results"]

    if candidates.empty:
        raise HTTPException(
            status_code = 404,
            detail      = filter_result["message"]
        )

    # Step 2: Build prompt
    try:
        prompt = build_prompt(user_query, candidates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 3: LLM call
    output = recommend(prompt, candidates)

    # Step 4: Enrich each recommendation with original dataset fields
    enriched = []
    for r in output["recommendations"]:
        name  = r.get("name", "")
        match = df[df["restaurant_name"].str.lower() == name.lower()]
        if match.empty:
            match = df[df["restaurant_name"].str.contains(name, case=False, na=False)]
        row_data = {}
        if not match.empty:
            best = match.sort_values("aggregate_rating", ascending=False).iloc[0]
            row_data = {
                "aggregate_rating": float(best.get("aggregate_rating", 0) or 0),
                "approx_cost"     : int(best.get("approx_cost", 0) or 0),
                "cuisines"        : str(best.get("cuisines", "") or ""),
                "votes"           : int(best.get("votes", 0) or 0),
                "online_order"    : str(best.get("online_order", "") or ""),
                "book_table"      : str(best.get("book_table", "") or ""),
            }
        enriched.append(RecommendationItem(**{**r, **row_data}))

    return RecommendationResponse(
        recommendations = enriched,
        source          = output["source"],
        filter_message  = filter_result["message"],
        count           = len(enriched),
        model_used      = GROQ_MODEL,
        error           = output.get("error"),
    )


# ---------------------------------------------------------------------------
# Serve frontend at /ui
# ---------------------------------------------------------------------------
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.isdir(_frontend_dir):
    app.mount("/ui", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
