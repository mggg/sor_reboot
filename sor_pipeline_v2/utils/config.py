"""Shared configuration: paths, state codes, thresholds, and covariate groupings.

These were previously hard-coded in several places across the notebooks. Centralizing
them here is what lets the national and tract drivers share the same logic.
"""

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

# --- Regions -----------------------------------------------------------------
REGIONS = {
    "contiguous_us": [
        "01",
        "04",
        "05",
        "06",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "40",
        "41",
        "42",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "50",
        "51",
        "53",
        "54",
        "55",
        "56",
    ],  # all contiguous states + DC
    # U.S. Census Bureau Official Regions
    "northeast": [
        "09",
        "23",
        "25",
        "33",
        "44",
        "50",  # New England: CT, ME, MA, NH, RI, VT
        "34",
        "36",
        "42",  # Mid-Atlantic: NJ, NY, PA
    ],
    "midwest": [
        "17",
        "18",
        "26",
        "39",
        "55",  # East North Central: IL, IN, MI, OH, WI
        "19",
        "20",
        "27",
        "29",
        "31",
        "38",
        "46",  # West North Central: IA, KS, MN, MO, NE, ND, SD
    ],
    "south": [
        "10",
        "12",
        "13",
        "24",
        "37",
        "45",
        "51",
        "11",
        "54",  # South Atlantic: DE, FL, GA, MD, NC, SC, VA, DC, WV
        "01",
        "21",
        "28",
        "47",  # East South Central: AL, KY, MS, TN
        "05",
        "22",
        "40",
        "48",  # West South Central: AR, LA, OK, TX
    ],
    "contiguous_west": [  # Excluding AK and HI because they are not part of the contiguous US
        "04",
        "08",
        "16",
        "30",
        "32",
        "35",
        "49",
        "56",  # Mountain: AZ, CO, ID, MT, NV, NM, UT, WY
        "06",
        "41",
        "53",  # Pacific (Contiguous): CA, OR, WA
    ],
}

if __name__ == "__main__":
    print(f"PKG_ROOT: {PKG_ROOT}")
    print(f"REPO_ROOT: {REPO_ROOT}")
