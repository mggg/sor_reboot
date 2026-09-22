"""How the geometry source is obtained: TIGER/Line 2020 downloads.

Each frame is downloaded once and cached to data/raw as GeoParquet with its
polygons intact; the loaders return only the attribute columns the dataset
uses. Anything spatial (maps, joins) reads the cached GeoParquet directly.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

from build_dataset.ingest.census_client import (
    COUNTY_GEOMETRY_2020_URL,
    TRACT_GEOMETRY_2020_URL_TEMPLATE,
)
from utils.config import RAW_DIR

GEOMETRY_ATTRS = ["GEOID", "NAME", "ALAND", "INTPTLAT", "INTPTLON"]


def load_county_geometry() -> pd.DataFrame:
    """County TIGER/Line 2020 attributes (polygons stay in the GeoParquet cache)."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / "county_geometry_2020.parquet"
    if not cache.exists():
        gdf = gpd.read_file(
            COUNTY_GEOMETRY_2020_URL
        )  # zipped shapefile, straight from the web
        gdf.to_parquet(cache)  # cache the FULL frame, polygons included
    return pd.DataFrame(gpd.read_parquet(cache)[GEOMETRY_ATTRS])


def load_tract_geometry(state_fips: str) -> pd.DataFrame:
    """Tract TIGER/Line 2020 attributes for one state (downloaded once, then cached)."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / f"tract_geometry_2020_{state_fips}.parquet"
    if not cache.exists():
        url = TRACT_GEOMETRY_2020_URL_TEMPLATE.format(state_fips=state_fips)
        gdf = gpd.read_file(url)
        gdf.to_parquet(cache)
    return pd.DataFrame(gpd.read_parquet(cache)[GEOMETRY_ATTRS])
