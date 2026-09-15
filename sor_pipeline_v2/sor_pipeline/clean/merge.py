"""Merge the four raw sources into one GeoDataFrame and apply basic cleaning.

Migrated from the merge portion of `3hispaniccleanjune` cell 3 (and the tract
equivalent). Joins PL + ACS + geometry + election on GEOID, renames raw census
codes via RENAME_DICT, derives CARIBBEAN / WHITEALONEORCOMBO / DENSITY / VOTELEAN,
and drops zero-land-area rows.
"""

from __future__ import annotations
import pandas as pd
from sor_pipeline.utils.config import COUNTY_GEOMETRY_URL
from sor_pipeline.ingest.census_api import (
    WHITE_TOTAL_COLS,
    NON_HISP_WHITE_TOTAL_COLS,
    RENAME_DICT,
)
import geopandas as gpd
import numpy as np


def add_geoid(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """Build GEOID from the FIPS component columns and drop them.

    level="county" -> state+county (5 digits); level="tract" -> state+county+tract (11).
    """
    parts = ["state", "county"] if level == "county" else ["state", "county", "tract"]
    df = df.copy()
    df["GEOID"] = df[parts].agg("".join, axis=1)
    return df.drop(columns=parts)


def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce every non-GEOID column to numeric (the API returns everything as strings)."""
    value_cols = [c for c in df.columns if c != "GEOID"]
    df[value_cols] = df[value_cols].apply(pd.to_numeric, errors="coerce")
    return df


def merge_sources(
    pl_total: pd.DataFrame,
    pl_hispanic: pd.DataFrame,
    acs: pd.DataFrame,
    geometry: pd.DataFrame,
    election: pd.DataFrame,
    level: str = "county",
) -> pd.DataFrame:
    # normalize each raw frame first
    pl_total = coerce_numeric(add_geoid(pl_total, level))
    pl_hispanic = coerce_numeric(add_geoid(pl_hispanic, level))
    acs = coerce_numeric(add_geoid(acs, level))

    # --- Merge the three Census tables ---
    pl_data = pd.merge(pl_total, pl_hispanic, on="GEOID", how="inner")
    census_data = pd.merge(pl_data, acs, on="GEOID", how="inner")

    # --- Load county geometry ---
    geometry = geometry.copy()
    geometry["GEOID"] = geometry["GEOID"].astype(str)

    # --- Merge geometry with Census data ---
    census_and_geodata = geometry.merge(census_data, on="GEOID", how="left")

    # --- Derive CARIBBEAN, WHITEALONEORCOMBO, NONHISPANICWHITEALONEORCOMBO ---
    census_and_geodata["CARIBBEAN"] = census_and_geodata[
        ["B03001_005E", "B03001_006E", "B03001_007E"]
    ].sum(axis=1)
    census_and_geodata["WHITEALONEORCOMBO"] = census_and_geodata[WHITE_TOTAL_COLS].sum(
        axis=1
    )
    census_and_geodata["NONHISPANICWHITEALONEORCOMBO"] = census_and_geodata[
        NON_HISP_WHITE_TOTAL_COLS
    ].sum(axis=1)

    # --- Rename raw census codes to human-readable names ---
    census_and_geodata.rename(columns=RENAME_DICT, inplace=True)

    # --- Merge 2020 presidential election data ---
    # `election` arrives from ingest already keyed on GEOID with standardized
    # E_20_PRES_DEM / E_20_PRES_REP columns (FIPS padding + renames happen in ingest/election.py).
    election = election.copy()

    # VOTELEAN: (Rep - Dem) / total two-party vote; positive = Republican-leaning.
    # Guard against divide-by-zero where a unit has no two-party votes.
    total = election["E_20_PRES_DEM"] + election["E_20_PRES_REP"]
    election["VOTELEAN"] = np.where(
        total == 0,
        np.nan,
        (election["E_20_PRES_REP"] - election["E_20_PRES_DEM"]) / total,
    )
    census_and_geodata = census_and_geodata.merge(
        election[["GEOID", "VOTELEAN", "E_20_PRES_DEM", "E_20_PRES_REP"]],
        on="GEOID",
        how="left",
    )

    # --- Final type formatting & derived geometry fields ---
    census_and_geodata["INTPTLON"] = census_and_geodata["INTPTLON"].astype(float)
    census_and_geodata["INTPTLAT"] = census_and_geodata["INTPTLAT"].astype(float)
    census_and_geodata["TOTALPOP"] = census_and_geodata["TOTALPOP"].astype(float)
    census_and_geodata["DENSITY"] = (
        census_and_geodata["TOTALPOP"] / census_and_geodata["ALAND"]
    )

    # Drop zero-land-area units (e.g. water-only) so density/geometry stay valid
    census_and_geodata = census_and_geodata[census_and_geodata["ALAND"] > 0].copy()

    return census_and_geodata
