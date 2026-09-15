import os

import pandas as pd
import requests
from dotenv import load_dotenv
from utils.config import ENV_PATH

load_dotenv(ENV_PATH)

# The Census API rejects requests asking for more than 50 variables at once.
# Larger variable lists are split into chunks of this size and re-joined on the
# geography key columns.
MAX_VARS_PER_REQUEST = 50

# --- Census API key ----------------------------------------------------------
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", None)
if not CENSUS_API_KEY:
    raise ValueError(
        "CENSUS_API_KEY environment variable not set. Please set it in your .env file."
    )


# --- Census API --------------------------------------------------------------
# The key is read from the CENSUS_API_KEY environment variable (see census_io.load_api_key).
DECENNIAL_PL_URL = "https://api.census.gov/data/2020/dec/pl"
ACS5_URL = "https://api.census.gov/data/2020/acs/acs5"
# Demographic and Housing Characteristics file. A third census product alongside
# PL and ACS: it carries the urban/rural classification (table P2), which the PL
# redistricting file does not publish and the ACS does not measure at all.
# Complete count, so no margins of error.
DECENNIAL_DHC_URL = "https://api.census.gov/data/2020/dec/dhc"
# Prior ACS 5-year vintage, used only to measure Hispanic population change.
# 2011-2015 shares NO years with 2016-2020, which is the Census Bureau's own
# condition for comparing two 5-year estimates: overlapping windows reuse the
# same responses and understate real change.
ACS5_PRIOR_URL = "https://api.census.gov/data/2015/acs/acs5"
COUNTY_GEOMETRY_URL = (
    "https://www2.census.gov/geo/tiger/TIGER2020/COUNTY/tl_2020_us_county.zip"
)
# Per-state tract geometry; format with a 2-digit state FIPS, e.g. .format(state_fips="06").
TRACT_GEOMETRY_URL_TEMPLATE = (
    "https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_{state_fips}_tract.zip"
)


def get_census_data(
    url: str, variables: list[str], for_geo: str, in_geo: str
) -> pd.DataFrame:
    """Fetch census data for a geography from a Census API endpoint.

    Parameters
    ----------
    url : str
        Base endpoint (Decennial PL or ACS 5-year).
    variables : list of str
        Census variable codes to request.
    for_geo, in_geo : str
        The `for=` / `in=` clauses, e.g. "county:*" / "state:*", or "tract:*" / "state:06".

    Returns
    -------
    pandas.DataFrame
        One row per geographic unit; values returned as strings.
    """
    if len(variables) > MAX_VARS_PER_REQUEST:
        chunks = [
            variables[i : i + MAX_VARS_PER_REQUEST]
            for i in range(0, len(variables), MAX_VARS_PER_REQUEST)
        ]
    else:
        chunks = [variables]
    merged: pd.DataFrame | None = None
    keys: list[str] = []

    for n, chunk in enumerate(chunks, start=1):
        params = {
            "get": ",".join(chunk),
            "for": for_geo,
            "in": in_geo,
            "key": CENSUS_API_KEY,
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {response.status_code}: {response.text}"
            )
        data = response.json()
        # data[0] is the header row; data[1:] are the records.
        frame = pd.DataFrame(data[1:], columns=data[0])
        frame = _build_geoid(frame)  # Add a GEOID column for easier merging later.
        frame.drop(columns=["state", "county", "tract"], inplace=True, errors="ignore")
        if merged is None:
            merged = frame
            continue
        before = len(merged)
        # Drop duplicate non-key columns (NAME comes back on every request and the GEOID is computed).
        # Without the drop, merge() would find the same column name in both frames and add a suffix to the new one, which is not what we want.
        overlap = [c for c in frame.columns if c in merged.columns and c != "GEOID"]
        merged = merged.merge(frame.drop(columns=overlap), on="GEOID", how="inner")
        if len(merged) != before:
            raise ValueError(
                f"batch {n} joined {len(merged)} rows against {before} -- "
                "chunks of one request disagree on geographies; refusing partial data"
            )
    return merged


def _build_geoid(df: pd.DataFrame) -> pd.DataFrame:
    """Add a `geoid` column to a DataFrame with `state`, `county`, and/or `tract` columns.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame with `state`, `county`, and/or `tract` columns.

    Returns
    -------
    pandas.DataFrame
        The same DataFrame with an additional `geoid` column.
    """
    if "tract" in df.columns:
        df["GEOID"] = df["state"] + df["county"] + df["tract"]
    elif "county" in df.columns:
        df["GEOID"] = df["state"] + df["county"]
    else:
        raise ValueError("DataFrame must have either 'tract' or 'county' columns.")
    return df
