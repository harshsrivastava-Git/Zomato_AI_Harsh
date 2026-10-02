"""
data/dataset_loader.py
Phase 2 -- Data Ingestion & Preprocessing
"""

import os
import sys
import pandas as pd
from datasets import load_dataset

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATASET_ID, DATASET_SPLIT, CLEAN_CSV, BUDGET_RANGES

# Actual columns in the HuggingFace dataset (discovered via exploration)
KEY_COLUMNS = [
    "name",
    "location",
    "cuisines",
    "approx_cost(for two people)",
    "rate",           # actual column name (not "aggregate rating")
    "votes",
    "online_order",
    "book_table",
]

RENAME_MAP = {
    "name":                        "restaurant_name",
    "approx_cost(for two people)": "approx_cost",
    "rate":                        "aggregate_rating",   # rename rate -> aggregate_rating
}


def _explore(df):
    """Print a quick summary of the raw dataset (ASCII-safe)."""
    print("\n[Explore] Shape          :", df.shape)
    print("[Explore] Columns        :", list(df.columns))
    print("[Explore] Null counts:\n", df.isnull().sum().to_string())
    print("-" * 60)


def _clean(df):
    """
    Cleaning steps (Phase 2):
      1. Retain key columns
      2. Rename to normalised names
      3. Drop rows with null restaurant_name / location / cuisines
      4. Normalise text to lowercase + strip
      5. Convert approx_cost to numeric (strip commas)
      6. Convert aggregate_rating to float (handle 'NEW', '-', '4.1/5' format)
      7. Convert votes to int
    """
    available = [c for c in KEY_COLUMNS if c in df.columns]
    df = df[available].copy()

    df.rename(columns={k: v for k, v in RENAME_MAP.items() if k in df.columns},
              inplace=True)

    critical = [c for c in ["restaurant_name", "location", "cuisines"] if c in df.columns]
    df.dropna(subset=critical, inplace=True)

    for col in ["restaurant_name", "location", "cuisines"]:
        if col in df.columns:
            df[col] = df[col].str.lower().str.strip()

    if "approx_cost" in df.columns:
        df["approx_cost"] = (
            df["approx_cost"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df["approx_cost"] = pd.to_numeric(df["approx_cost"], errors="coerce")
        df["approx_cost"] = df["approx_cost"].fillna(0).astype(int)

    if "aggregate_rating" in df.columns:
        # Rate column looks like "4.1/5", "NEW", "-", "3.8/5"
        df["aggregate_rating"] = (
            df["aggregate_rating"]
            .astype(str)
            .str.strip()
            .str.replace("/5", "", regex=False)   # strip "/5" suffix
            .replace({"NEW": None, "-": None, "nan": None, "": None})
        )
        df["aggregate_rating"] = pd.to_numeric(df["aggregate_rating"], errors="coerce")
        df["aggregate_rating"] = df["aggregate_rating"].fillna(0.0)

    if "votes" in df.columns:
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

    df.reset_index(drop=True, inplace=True)
    return df


def _save_cache(df):
    """Save cleaned DataFrame to CSV."""
    cache_path = os.path.join(os.path.dirname(__file__), "..", CLEAN_CSV)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    df.to_csv(cache_path, index=False, encoding="utf-8")
    print(f"[Cache] Saved -> {os.path.abspath(cache_path)}")


def load_and_preprocess(force_reload=False, verbose=True):
    """
    Main entry point for Phase 2.
    Returns a clean Pandas DataFrame ready for the filter engine.
    """
    cache_path = os.path.join(os.path.dirname(__file__), "..", CLEAN_CSV)

    if not force_reload and os.path.exists(cache_path):
        print(f"[Loader] Loading from cache: {cache_path}")
        df = pd.read_csv(cache_path)
        print(f"[Loader] Loaded {len(df):,} rows from cache.")
        return df

    print(f"[Loader] Downloading dataset: {DATASET_ID} ...")
    ds = load_dataset(DATASET_ID)
    df_raw = ds[DATASET_SPLIT].to_pandas()
    print(f"[Loader] Raw dataset: {df_raw.shape[0]:,} rows, {df_raw.shape[1]} columns.")

    if verbose:
        _explore(df_raw)

    print("[Loader] Cleaning dataset ...")
    df_clean = _clean(df_raw)
    print(f"[Loader] After cleaning: {len(df_clean):,} rows.")

    for col in ["restaurant_name", "location", "cuisines"]:
        if col in df_clean.columns:
            nulls = df_clean[col].isnull().sum()
            status = "OK" if nulls == 0 else f"WARNING: {nulls} nulls"
            print(f"[Verify] {col:20s} -> {status}")

    _save_cache(df_clean)
    return df_clean


if __name__ == "__main__":
    df = load_and_preprocess(force_reload=True, verbose=True)
    print("\n[Result] Final DataFrame:")
    print(f"  Shape  : {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(f"\n  Budget distribution:")
    for label, (lo, hi) in BUDGET_RANGES.items():
        count = ((df["approx_cost"] >= lo) & (df["approx_cost"] < hi)).sum()
        print(f"    {label:8s} (Rs.{lo}-{hi}): {count:,} restaurants")
    print(f"\n  Rating stats: min={df['aggregate_rating'].min()}, "
          f"max={df['aggregate_rating'].max()}, "
          f"mean={df['aggregate_rating'].mean():.2f}")
