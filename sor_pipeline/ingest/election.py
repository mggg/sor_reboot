"""Load the 2020 presidential election CSVs (county nationwide, or tract per state).

Migrated from the election-merge blocks in `3hispaniccleanjune` cell 3
(`county_level_2020.csv`) and `statetractcleanedjune` cell 3
(`<STATE>_tract_election_and_pop_data.csv`).

This module only reads the raw CSV and normalizes FIPS/GEOID. VOTELEAN and other
derived fields belong to the clean stage.
"""

from __future__ import annotations
import pandas as pd
from sor_pipeline.utils.config import RAW_DIR


def load_county_election() -> pd.DataFrame:
    """Read county_level_2020.csv -> GEOID + standardized two-party vote columns."""
    df = pd.read_csv(RAW_DIR / "county_level_2020.csv")
    df = df.copy()  # avoid SettingWithCopyWarning
    df["GEOID"] = (
        df["county_fips"].astype(str).apply(lambda x: "0" + x if len(x) == 4 else x)
    )
    return df.rename(
        columns={"E_20_PRES_Dem": "E_20_PRES_DEM", "E_20_PRES_Rep": "E_20_PRES_REP"}
    )[
        ["GEOID", "E_20_PRES_DEM", "E_20_PRES_REP"]
    ]  # Standardized column names for consistency with tract-level data.


def load_tract_election(state: str) -> pd.DataFrame:
    """Read <STATE>_tract_election_and_pop_data.csv -> GEOID + standardized vote columns."""
    df = pd.read_csv(RAW_DIR / f"{state}_tract_election_and_pop_data.csv")
    df = df.copy()  # avoid SettingWithCopyWarning
    df["GEOID"] = (
        df["tract"].astype(str).apply(lambda x: "0" + x if len(x) == 10 else x)
    )
    return df.rename(
        columns={"pres_20_dem": "E_20_PRES_DEM", "pres_20_rep": "E_20_PRES_REP"}
    )[
        [
            "GEOID",
            "E_20_PRES_DEM",
            "E_20_PRES_REP",
        ]  # Standardized column names for consistency with county-level data.
    ]
