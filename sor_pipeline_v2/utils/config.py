"""Shared configuration: paths, state codes, thresholds, and covariate groupings.

These were previously hard-coded in several places across the notebooks. Centralizing
them here is what lets the national and tract drivers share the same logic.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

ENV_PATH = "/Users/esher/mggg/projects/sor/sor/.env"  # replace with your own path to the .env file!

success = load_dotenv(ENV_PATH)

if not success:
    print(
        "No .env file found. Make sure to set the CENSUS_API_KEY environment variable."
    )

# --- Figures -----------------------------------------------------------------
# Resolution for every saved raster figure; nothing in the pipeline goes below it.
FIGURE_DPI = 300

# --- Paths -------------------------------------------------------------------
# Resolve relative to this package so scripts work regardless of CWD.
PKG_ROOT = Path(__file__).resolve().parent

DATA_DIR = (
    PKG_ROOT.parent / "data"
)  # data lives in the parent of the repo root (separate from code)

NATIONAL_DIR = DATA_DIR / "national"

RAW_NATIONAL_DIR = NATIONAL_DIR / "raw"

# The lab's GerryDB release: one geopackage per state per geography level,
# delivered as files rather than fetched. Read-only input the build never
# writes to, and the only source of tract-level election returns.
GERRYDB_RELEASE_DIR = DATA_DIR / "RELEASE_geopackages"

# Durable records ABOUT the raw sources: what each file's bytes hashed
# to, and which published release a download came from. Its own directory,
# outside DATA_DIR, because the whole job of these records is to outlive
# the downloads they describe -- a record kept beside a 10 GB archive dies
# with it, and a checksum cannot be verified from inside the directory
# being verified.
SOURCE_RECORDS_DIR = PKG_ROOT.parent / "source_records"

RAW_NATIONAL_COUNTIES_PARQUET = NATIONAL_DIR / "counties" / "raw.parquet"

PROCESSED_NATIONAL_COUNTIES_PARQUET = NATIONAL_DIR / "counties" / "processed.parquet"

RAW_NATIONAL_TRACTS_PARQUET = NATIONAL_DIR / "tracts" / "raw.parquet"

PROCESSED_NATIONAL_TRACTS_PARQUET = NATIONAL_DIR / "tracts" / "processed.parquet"

# The 52 jurisdictions the decennial PL file covers -- the 50 states, DC,
# and Puerto Rico -- which is exactly the set of two-digit prefixes on the
# county spine's 3,221 GEOIDs. A tract pull visits them one at a time
# because the API refuses a state wildcard below county level.
TRACT_PULL_STATE_FIPS: tuple[str, ...] = (
    "01",
    "02",
    "04",
    "05",
    "06",
    "08",
    "09",
    "10",
    "11",
    "12",
    "13",
    "15",
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
    "72",
)

# Two-digit state FIPS -> USPS abbreviation, for the 50 states, DC and PR.
# Lives here because both arms need it: SHAP county labels and the VEST
# precinct filenames, which are keyed by lowercase abbreviation.
STATE_FIPS_TO_USPS: dict[str, str] = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
    "72": "PR",
}

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


# Full names, for anything a person reads: a report title saying
# "California tracts" beats one saying "processed_states-06.parquet".
# USPS codes live in STATE_FIPS_TO_USPS and stay the key for filenames.
STATE_FIPS_TO_NAME: dict[str, str] = {
    "01": "Alabama",
    "02": "Alaska",
    "04": "Arizona",
    "05": "Arkansas",
    "06": "California",
    "08": "Colorado",
    "09": "Connecticut",
    "10": "Delaware",
    "11": "District of Columbia",
    "12": "Florida",
    "13": "Georgia",
    "15": "Hawaii",
    "16": "Idaho",
    "17": "Illinois",
    "18": "Indiana",
    "19": "Iowa",
    "20": "Kansas",
    "21": "Kentucky",
    "22": "Louisiana",
    "23": "Maine",
    "24": "Maryland",
    "25": "Massachusetts",
    "26": "Michigan",
    "27": "Minnesota",
    "28": "Mississippi",
    "29": "Missouri",
    "30": "Montana",
    "31": "Nebraska",
    "32": "Nevada",
    "33": "New Hampshire",
    "34": "New Jersey",
    "35": "New Mexico",
    "36": "New York",
    "37": "North Carolina",
    "38": "North Dakota",
    "39": "Ohio",
    "40": "Oklahoma",
    "41": "Oregon",
    "42": "Pennsylvania",
    "44": "Rhode Island",
    "45": "South Carolina",
    "46": "South Dakota",
    "47": "Tennessee",
    "48": "Texas",
    "49": "Utah",
    "50": "Vermont",
    "51": "Virginia",
    "53": "Washington",
    "54": "West Virginia",
    "55": "Wisconsin",
    "56": "Wyoming",
    "72": "Puerto Rico",
}

# Which dataset a build produces and a model fits on. Here rather than in
# main_build so the regression can name a level without importing a driver.
GeographicBuildLevel = Literal["national_counties", "national_tracts"]


def tract_parquet_paths(state_fips: Sequence[str] | None) -> tuple[Path, Path]:
    """Where a tract build of `state_fips` writes its raw and processed frames.

    A build of every jurisdiction owns the national filenames. A subset
    carries its states in the filename instead, so a one-state run cannot
    overwrite the national dataset -- the same reason the raw source
    caches carry their scope in their names.

    Parameters
    ----------
    state_fips : sequence of str or None
        The states being built; None means all of TRACT_PULL_STATE_FIPS.

    Returns
    -------
    tuple of (Path, Path)
        The raw and processed parquet paths, in that order.
    """
    if state_fips is None or set(state_fips) == set(TRACT_PULL_STATE_FIPS):
        return RAW_NATIONAL_TRACTS_PARQUET, PROCESSED_NATIONAL_TRACTS_PARQUET
    label = "states-" + "-".join(sorted(set(state_fips)))
    tract_dir = NATIONAL_DIR / "tracts"
    return tract_dir / f"raw_{label}.parquet", tract_dir / f"processed_{label}.parquet"


def describe_geography_in_eng(
    geo_level: GeographicBuildLevel, state_fips: Sequence[str] | None = None
) -> str:
    """The geography in words: "California tracts", "US counties".

    Parameters
    ----------
    geo_level : GeographicBuildLevel
        Which dataset.
    state_fips : sequence of str or None
        Tracts only: the state scope. None means all of them.

    Returns
    -------
    str
        e.g. "California tracts", "US tracts", "US counties".
    """
    if geo_level == "national_counties":
        return "US counties"
    if not state_fips:
        return "US tracts"
    names = [STATE_FIPS_TO_NAME[fips] for fips in sorted(state_fips)]
    return f"{', '.join(names)} tracts"


def processed_parquet_path(
    level: GeographicBuildLevel, state_fips: Sequence[str] | None = None
) -> Path:
    """The processed frame a level fits on; for tracts, of a state scope.

    Parameters
    ----------
    level : GeographicBuildLevel
        "national_counties" or "national_tracts".
    state_fips : sequence of str or None
        Tracts only: which states the frame covers. None means all of
        them, i.e. the national tract file. Ignored for counties, which
        are a single national build.

    Returns
    -------
    Path
        The processed parquet to read.
    """
    if level == "national_counties":
        return PROCESSED_NATIONAL_COUNTIES_PARQUET
    return tract_parquet_paths(state_fips)[1]


if __name__ == "__main__":
    print(f"PKG_ROOT: {PKG_ROOT}")
    print(f"DATA_DIR: {DATA_DIR}")
