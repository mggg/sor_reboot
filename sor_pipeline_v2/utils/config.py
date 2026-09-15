"""Shared configuration: paths, state codes, thresholds, and covariate groupings.

These were previously hard-coded in several places across the notebooks. Centralizing
them here is what lets the national and tract drivers share the same logic.
"""

import os
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = "/Users/esher/mggg/projects/sor/sor/.env"  # replace with your own path to the .env file!

success = load_dotenv(ENV_PATH)

if not success:
    print(
        "No .env file found. Make sure to set the CENSUS_API_KEY environment variable."
    )

# --- Paths -------------------------------------------------------------------
# Resolve relative to this package so scripts work regardless of CWD.
PKG_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PKG_ROOT.parent

DATA_DIR = (
    REPO_ROOT.parent / "data"
)  # data lives in the parent of the repo root (separate from code)
RAW_DIR = DATA_DIR / "raw"

PROCESSED_NATIONAL_COUNTIES_PARQUET = (
    DATA_DIR / "national_counties" / "processed.parquet"
)

if __name__ == "__main__":
    print(f"PKG_ROOT: {PKG_ROOT}")
    print(f"REPO_ROOT: {REPO_ROOT}")
