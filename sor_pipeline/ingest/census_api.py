"""Census Data API access (Decennial PL + ACS 5-year).

Migrated from `3hispaniccleanjune` cells 2-3 and `statetractcleanedjune` cells 2-3.
"""

from __future__ import annotations
import os
import pandas as pd
from dotenv import load_dotenv
import requests
from sor_pipeline.utils.config import DECENNIAL_PL_URL, ACS5_URL, CENSUS_API_KEY

# Census variable code lists. Kept here because they define what gets fetched.
# (Filled in during migration from the notebook's `vars_2020` / `vars_2020_hisp` /
# `acs_list` / `white_total_cols` / `non_hisp_white_total_cols` / `rename_dict`.)
VARS_PL_TOTAL: list[str] = [
    "P1_001N",
    "P1_003N",
    "P1_004N",
    "P1_008N",
    "P1_011N",
    "P1_012N",
    "P1_013N",
    "P1_014N",
    "P1_015N",
    "P1_027N",
    "P1_028N",
    "P1_029N",
    "P1_030N",
    "P1_031N",
    "P1_032N",
    "P1_033N",
    "P1_034N",
    "P1_035N",
    "P1_036N",
    "P1_048N",
    "P1_049N",
    "P1_050N",
    "P1_051N",
    "P1_052N",
    "P1_053N",
    "P1_054N",
    "P1_055N",
    "P1_056N",
    "P1_057N",
    "P1_064N",
    "P1_065N",
    "P1_066N",
    "P1_067N",
    "P1_068N",
    "P1_071N",
]  # P1 tables: total-population race counts
VARS_PL_HISPANIC: list[str] = [
    "P2_002N",
    "P2_005N",
    "P2_006N",
    "P2_010N",
    "P2_013N",
    "P2_014N",
    "P2_015N",
    "P2_016N",
    "P2_017N",
    "P2_029N",
    "P2_030N",
    "P2_031N",
    "P2_032N",
    "P2_033N",
    "P2_034N",
    "P2_035N",
    "P2_036N",
    "P2_037N",
    "P2_038N",
    "P2_050N",
    "P2_051N",
    "P2_052N",
    "P2_053N",
    "P2_054N",
    "P2_055N",
    "P2_056N",
    "P2_057N",
    "P2_058N",
    "P2_059N",
    "P2_066N",
    "P2_067N",
    "P2_068N",
    "P2_069N",
    "P2_070N",
    "P2_073N",
]
VARS_ACS: list[str] = [
    "B01001_001E",  # Total population (ACS)
    "B19013_001E",  # Median household income
    "B15003_022E",  # Bachelor's degree
    "C16002_004E",  # Spanish-speaking limited-English ("linguistic isolation")
    "B05002_013E",  # Foreign born (non-citizen)
    "B03001_004E",  # Mexican origin
    # --- Caribbean origin components ---
    "B03001_005E",  # Puerto Rican
    "B03001_006E",  # Cuban
    "B03001_007E",  # Dominican
    "B03001_016E",  # South American
    "B03001_008E",  # Central American
    "B28002_013E",  # No internet access
    "B01002_001E",  # Median age (simple proxy for generation)
    "B25003_003E",  # Renter-occupied units
    "B05001_006E",  # Not a U.S. citizen (status often affects racial self-ID)
    "B29001_001E",  # Voting-age population
]  # ACS 5-year socioeconomic covariates
WHITE_TOTAL_COLS: list[str] = [
    "P1_003N",
    "P1_011N",
    "P1_012N",
    "P1_013N",
    "P1_014N",
    "P1_015N",
    "P1_027N",
    "P1_028N",
    "P1_029N",
    "P1_030N",
    "P1_031N",
    "P1_032N",
    "P1_033N",
    "P1_034N",
    "P1_035N",
    "P1_036N",
    "P1_048N",
    "P1_049N",
    "P1_050N",
    "P1_051N",
    "P1_052N",
    "P1_053N",
    "P1_054N",
    "P1_055N",
    "P1_056N",
    "P1_057N",
    "P1_064N",
    "P1_065N",
    "P1_066N",
    "P1_067N",
    "P1_068N",
    "P1_071N",
]  # PL columns summed into WHITEALONEORCOMBO
NON_HISP_WHITE_TOTAL_COLS: list[str] = [
    "P2_005N",
    "P2_013N",
    "P2_014N",
    "P2_015N",
    "P2_016N",
    "P2_017N",
    "P2_029N",
    "P2_030N",
    "P2_031N",
    "P2_032N",
    "P2_033N",
    "P2_034N",
    "P2_035N",
    "P2_036N",
    "P2_037N",
    "P2_038N",
    "P2_050N",
    "P2_051N",
    "P2_052N",
    "P2_053N",
    "P2_054N",
    "P2_055N",
    "P2_056N",
    "P2_057N",
    "P2_058N",
    "P2_059N",
    "P2_066N",
    "P2_067N",
    "P2_068N",
    "P2_069N",
    "P2_070N",
    "P2_073N",
]  # Non-Hispanic White-alone-or-in-combination columns summed into WHITEALONEORCOMBO
RENAME_DICT: dict[str, str] = {
    "P1_001N": "TOTALPOP",
    "P1_003N": "WHITEALONE",
    "P1_008N": "SORALONE",
    "P1_015N": "WHITESOR",
    "P2_002N": "HISPANIC",
    "P2_005N": "NONHISPANICWHITEALONE",
    "P2_010N": "NONHISPANICSORALONE",
    "P2_017N": "NONHISPANICWHITESOR",
    "B01001_001E": "ACSTOTALPOP",
    "B15003_022E": "BACHDEG",
    "C16002_004E": "SPANISHLIMENGLISH",
    "B05002_013E": "FOREIGNBORN",
    "B03001_004E": "MEXICANORIGIN",
    "B03001_016E": "SOUTHAMORIGIN",
    "B03001_008E": "CENTRALAMORIGIN",
    "B28002_013E": "NOINTERNET",
    "B01002_001E": "MEDAGE",
    "B25003_003E": "RENTERS",
    "B05001_006E": "NONCITIZENS",
    "B19013_001E": "MEDINCOME",
    "B29001_001E": "VOTINGAGEPOP",
}  # raw census code -> human-readable name


def verify_api_key() -> str:
    """Return the Census API key from the CENSUS_API_KEY environment variable.

    Raises a clear error if unset, rather than failing silently the way the
    notebook's `os.environ.get(...)` fallback does.
    """
    if not CENSUS_API_KEY:
        raise ValueError(
            "CENSUS_API_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    return CENSUS_API_KEY


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
    params = {
        "get": ",".join(variables),
        "for": for_geo,
        "in": in_geo,
        "key": CENSUS_API_KEY,
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception(
            f"API Request failed with status code {response.status_code}: {response.text}"
        )

    data = response.json()
    # data[0] is the header row; data[1:] are the records.
    return pd.DataFrame(data[1:], columns=data[0])


def fetch_decennial_pl(for_geo: str, in_geo: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch the P1 (total race) and P2 (Hispanic-by-race) tables.

    Parameters
    ----------
    for_geo : str
        The `for=` clause, e.g. "county:*" or "tract:*".
    in_geo : str
        The `in=` clause, e.g. "state:*" or "state:06".

    Returns
    -------
    tuple of pandas.DataFrame
        Two frames: (pl_total, pl_hispanic), each with one row per geographic unit; values returned as strings.
    """

    print("Fetching 2020 Decennial PL data...")
    pl_total = get_census_data(DECENNIAL_PL_URL, VARS_PL_TOTAL, for_geo, in_geo)
    pl_hispanic = get_census_data(DECENNIAL_PL_URL, VARS_PL_HISPANIC, for_geo, in_geo)
    print("Done fetching 2020 Decennial PL data.")
    return pl_total, pl_hispanic


def fetch_acs(for_geo: str, in_geo: str) -> pd.DataFrame:
    """Fetch the ACS 5-year socioeconomic covariates.

    Parameters
    ----------
    for_geo : str
        The `for=` clause, e.g. "county:*" or "tract:*".
    in_geo : str
        The `in=` clause, e.g. "state:*" or "state:06".

    Returns
    -------
    pandas.DataFrame
        One row per geographic unit; values returned as strings.
    """
    print("Fetching 2020 ACS 5-Year data...")
    df_acs = get_census_data(ACS5_URL, VARS_ACS, for_geo, in_geo)
    print("Done fetching 2020 ACS 5-Year data.")
    return df_acs
