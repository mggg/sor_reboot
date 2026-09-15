"""TIGER/Line 2020 geometry download (county nationwide, or tract per state).

Migrated from the `gpd.read_file(url)` calls in `3hispaniccleanjune` cell 3 and
`statetractcleanedjune` cell 3.

Geometry is a GeoDataFrame of polygons read straight from the Census TIGER zip,
not a local CSV. Each frame is downloaded once and cached to data/raw as
GeoParquet, then reused on later runs.
"""

from __future__ import annotations
import geopandas as gpd
from sor_pipeline.utils.config import (
    COUNTY_GEOMETRY_URL,
    TRACT_GEOMETRY_URL_TEMPLATE,
    RAW_DIR,
)


def load_county_geometry() -> gpd.GeoDataFrame:
    """County TIGER/Line 2020 geometry (downloaded once, then cached in data/raw)."""
    if not RAW_DIR.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / "county_geometry_2020.parquet"
    if cache.exists():
        # print(f"Loading county geometry from cache: {cache}")
        return gpd.read_parquet(cache)
    gdf = gpd.read_file(COUNTY_GEOMETRY_URL)  # zipped shapefile, straight from the web
    gdf.to_parquet(cache)
    return gdf


def load_tract_geometry(state_fips: str) -> gpd.GeoDataFrame:
    """Tract TIGER/Line 2020 geometry for one state (downloaded once, then cached)."""
    cache = RAW_DIR / f"tract_geometry_2020_{state_fips}.parquet"
    if cache.exists():
        return gpd.read_parquet(cache)
    url = TRACT_GEOMETRY_URL_TEMPLATE.format(state_fips=state_fips)
    gdf = gpd.read_file(url)
    gdf.to_parquet(cache)
    return gdf
