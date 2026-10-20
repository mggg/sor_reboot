import os
from dataclasses import dataclass

import pandas as pd
import requests
from dotenv import load_dotenv

from utils.config import ENV_PATH

load_dotenv(ENV_PATH)

# The Census API rejects requests asking for more than 50 variables at once.
MAX_VARS_PER_REQUEST = 50


@dataclass(frozen=True)
class GeoScope:
    """One query scope: the API clauses plus the name its cache file carries."""

    for_geo: str
    in_geo: str
    geography_label: str


NATIONAL_COUNTIES = GeoScope("county:*", "state:*", "national_counties")


def state_tracts(state_fips: str) -> GeoScope:
    """Every tract in one state.

    `for` names the level the rows come back at, `in` the parent that
    bounds the search -- census geography nests state > county > tract.
    One state at a time because the API refuses a state wildcard below
    county level: `in=state:*` with `for=tract:*` answers 400 "wildcard
    not allowed for 'state' in geography hierarchy".

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code, e.g. "06".

    Returns
    -------
    GeoScope
        The tract scope for that state, labelled for its own cache file.
    """
    return GeoScope(
        for_geo="tract:*",
        in_geo=f"state:{state_fips}",
        geography_label=f"tracts_{state_fips}",
    )


# --- Census API key ----------------------------------------------------------
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", None)
if not CENSUS_API_KEY:
    raise ValueError(
        "CENSUS_API_KEY environment variable not set. Please set it in your .env file."
    )

# Endpoint URLs live with their consumers (each has exactly one): the
# PL/ACS/DHC endpoints in their api modules, the TIGER URLs in geometry_api.


def get_census_data(
    source_url: str, feature_codes: list[str], for_geo: str, in_geo: str
) -> pd.DataFrame:
    """Fetch census data for a geography from a Census API endpoint.

    Parameters
    ----------
    source_url : str
        Base endpoint (Decennial PL or ACS 5-year).
    feature_codes : list of str
        Census variable codes to request.
    for_geo, in_geo : str
        The `for=` / `in=` clauses, e.g. "county:*" / "state:*", or "tract:*" / "state:06".

    Returns
    -------
    pandas.DataFrame
        One row per geographic unit; values returned as strings. Returns an empty DataFrame if no data was fetched.

    Raises
    ------
    ValueError
        If the API answers any batch with a non-200 status, or if two
        batches of one request disagree on the set of geographies (partial
        data is refused rather than merged).
    requests.RequestException
        Propagated on network failure.
    """
    if len(feature_codes) > MAX_VARS_PER_REQUEST:
        chunks = [
            feature_codes[i : i + MAX_VARS_PER_REQUEST]
            for i in range(0, len(feature_codes), MAX_VARS_PER_REQUEST)
        ]
    else:
        chunks = [feature_codes]
    merged: pd.DataFrame | None = None

    for n, chunk in enumerate(chunks, start=1):
        params = {
            "get": ",".join(chunk),
            "for": for_geo,
            "in": in_geo,
            "key": CENSUS_API_KEY,
        }
        response = requests.get(source_url, params=params)
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
    if merged is None:
        merged = pd.DataFrame()
    return merged


def _build_geoid(df: pd.DataFrame) -> pd.DataFrame:
    """Add a `GEOID` column to a DataFrame with `state`, `county`, and/or `tract` columns.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame with `state`, `county`, and/or `tract` columns.

    Returns
    -------
    pandas.DataFrame
        The same DataFrame with an additional `GEOID` column (state +
        county [+ tract], concatenated as strings).

    Raises
    ------
    ValueError
        If the DataFrame has neither a `county` nor a `tract` column.
    """
    if "tract" in df.columns:
        df["GEOID"] = df["state"] + df["county"] + df["tract"]
    elif "county" in df.columns:
        df["GEOID"] = df["state"] + df["county"]
    else:
        raise ValueError("DataFrame must have either 'tract' or 'county' columns.")
    return df
