"""Shared configuration: paths, state codes, thresholds, and covariate groupings.

These were previously hard-coded in several places across the notebooks. Centralizing
them here is what lets the national and tract drivers share the same logic.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

success = load_dotenv("/Users/esher/mggg/projects/sor/sor/.env")

if not success:
    print(
        "No .env file found. Make sure to set the CENSUS_API_KEY environment variable."
    )

# --- Paths -------------------------------------------------------------------
# Resolve relative to this package so scripts work regardless of CWD.
PKG_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PKG_ROOT.parent

# Source inputs that already live in the repo (election CSVs the notebooks read).
SOURCE_DIR = REPO_ROOT / "hispanicrace"

# Data tree. Lives at the REPO ROOT (a sibling of the sor_pipeline/ code package), NOT
# inside it — outputs stay cleanly separated from code. RAW holds acquired inputs
# (census/geometry cache, election CSVs); every analysis result is grouped by driver ->
# section, so each folder holds its own README, figures, and data files together.
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

# --- States ------------------------------------------------------------------
# FIPS codes for the four tract-level states; the tract driver runs one at a time.
# (Defined before the output paths below because the run directory name is derived
# from EXCLUDE_STATES and the clustering thresholds.)
STATE_FIPS = {"CA": "06", "TX": "48", "FL": "12", "NY": "36"}

# Non-contiguous states / territories excluded from the national spatial analysis.
# EXCLUDE_STATES = ["02", "15", "72", "60", "66", "69", "78"]

# Exclude most territories from the national spatial analysis (keep AK, HI, and PR)
EXCLUDE_STATES = ["60", "66", "69", "78"]


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
    "alaska": ["02"],
    "hawaii": ["15"],
    "puerto_rico": ["72"],
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

# --- Clustering threshold (spatial.py) ---------------------------------------
# Minimum Hispanic population per cluster: units below it are merged with neighbors
# until the cluster clears it; units at/above it stand alone. 0 disables clustering
# entirely (every unit is its own cluster).
MIN_CLUSTER_HISPANIC = 36
MIN_SPATIAL_UNITS = 30  # The minimum number of spatial units for Moran and CAPY to produce meaningful results. If the number of spatial units is below this threshold, the analysis will be skipped.
TRACT_MIN_POP = {"CA": 90, "TX": 90, "FL": 20, "NY": 10}

# --- run_national outputs (data/national/<run slug>/<section>/) ---------------
# Each parameter combination gets its own output directory so re-running with a
# different exclusion list or clustering threshold never overwrites earlier results.
# The slug encodes every parameter that shapes the analysis outputs.
RUN_SLUG = (
    f"excl-{'-'.join(EXCLUDE_STATES) if EXCLUDE_STATES else 'none'}"
    f"_minpop-{MIN_CLUSTER_HISPANIC}"
)

NATIONAL_DIR = DATA_DIR / "national"
NATIONAL_RUN_DIR = NATIONAL_DIR / RUN_SLUG
NATIONAL_SCATTER_DIR = NATIONAL_RUN_DIR / "scatter"
NATIONAL_SCATTER_COVARIATE_DIR = NATIONAL_SCATTER_DIR / "by_covariate"
NATIONAL_SPATIAL_DIR = NATIONAL_RUN_DIR / "spatial"
NATIONAL_LOGISTIC_DIR = NATIONAL_RUN_DIR / "logistic"

# The processed dataset is parameter-independent (ingest -> clean -> features uses
# every state), so it stays shared at the national level rather than per-run.
PARQUET_PATH = NATIONAL_DIR / "dataset.parquet"
CORRELATIONS_PATH = NATIONAL_SCATTER_DIR / "correlations.csv"
LOGISTIC_PATH = NATIONAL_LOGISTIC_DIR / "univariate_logistic.csv"


def write_run_readme() -> None:
    """Write README.md at the run directory root recording this run's parameters.

    Overwrites on every run: the README always reflects the config that produced
    (or last refreshed) the directory's contents.
    """
    NATIONAL_RUN_DIR.mkdir(parents=True, exist_ok=True)
    excluded = ", ".join(EXCLUDE_STATES) if EXCLUDE_STATES else "none"
    (NATIONAL_RUN_DIR / "README.md").write_text(
        f"# National run: `{RUN_SLUG}`\n\n"
        "Outputs in this directory were produced with the following configuration\n"
        "(`sor_pipeline/utils/config.py`):\n\n"
        "| Parameter | Value |\n"
        "| --- | --- |\n"
        f"| Excluded state/territory FIPS (`EXCLUDE_STATES`) | {excluded} |\n"
        f"| Minimum Hispanic population per cluster (`MIN_CLUSTER_HISPANIC`; 0 = no clustering) | {MIN_CLUSTER_HISPANIC} |\n"
        f"| Random seed (`RANDOM_STATE`) | {RANDOM_STATE} |\n\n"
        "The processed dataset is parameter-independent and shared across runs at\n"
        "[`../dataset.parquet`](../dataset.parquet).\n\n"
        "Sections: [`scatter/`](scatter/), [`spatial/`](spatial/), "
        "[`logistic/`](logistic/).\n"
    )


# --- run_prediction outputs (data/prediction/<section>/) ---------------------
PREDICTION_DIR = DATA_DIR / "prediction"
CLASSIFICATION_DIR = PREDICTION_DIR / "classification"
REGRESSION_DIR = PREDICTION_DIR / "regression"  # RF regression + SHAP
DEPENDENCE_DIR = REGRESSION_DIR / "dependence"  # SHAP dependence/interaction plots
ALTERNATIVE_DIR = REGRESSION_DIR / "alternative"  # 6.C polynomial + logit Lasso
LOGRATIO_DIR = REGRESSION_DIR / "log_ratio"  # 6.D log-ratio Ridge/Lasso

CLASSIFICATION_METRICS_PATH = CLASSIFICATION_DIR / "metrics.csv"
CLASSIFICATION_LOGIT_PATH = CLASSIFICATION_DIR / "logistic_importance.csv"
CLASSIFICATION_RF_PATH = CLASSIFICATION_DIR / "rf_importance.csv"
REGRESSION_METRICS_PATH = REGRESSION_DIR / "metrics.csv"
REGRESSION_SHAP_PATH = REGRESSION_DIR / "shap_importance.csv"

# --- run_tract outputs (data/tract/<STATE>/<section>/) -----------------------
# Per-state paths are built in the driver: see run_tract.state_paths().
TRACT_DIR = DATA_DIR / "tract"

# --- Census API --------------------------------------------------------------
# The key is read from the CENSUS_API_KEY environment variable (see census_io.load_api_key).
DECENNIAL_PL_URL = "https://api.census.gov/data/2020/dec/pl"
ACS5_URL = "https://api.census.gov/data/2020/acs/acs5"
COUNTY_GEOMETRY_URL = (
    "https://www2.census.gov/geo/tiger/TIGER2020/COUNTY/tl_2020_us_county.zip"
)
# Per-state tract geometry; format with a 2-digit state FIPS, e.g. .format(state_fips="06").
TRACT_GEOMETRY_URL_TEMPLATE = (
    "https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_{state_fips}_tract.zip"
)

# --- Census API key ----------------------------------------------------------
CENSUS_API_KEY = os.environ.get(
    "CENSUS_API_KEY",
    # YOUR-KEY-HERE,
)

# --- Covariate groupings (features.py / modeling.py) -------------------------
# Count covariates get a log / log1p transform; the rest are used as-is.
VARS_LOG = [
    "DENSITY",
    "BACHDEG",
    "SPANISHLIMENGLISH",
    "FOREIGNBORN",
    "MEXICANORIGIN",
    "SOUTHAMORIGIN",
    "CENTRALAMORIGIN",
    "CARIBBEAN",
    "NOINTERNET",
    "RENTERS",
    "NONCITIZENS",
    "MEDINCOME",
    "NUMBEROFVOTERS",
]
VARS_NO_LOG = ["MEDAGE", "VOTELEAN", "INTPTLON"]

# Random seed used for every train/test split in the modeling stage.
RANDOM_STATE = 42

Y_VARS = [
    "Hisp SOR Alone PL Percent",
    "Hisp White SOR PL Percent",
    "Hisp White Alone PL Percent",
]
