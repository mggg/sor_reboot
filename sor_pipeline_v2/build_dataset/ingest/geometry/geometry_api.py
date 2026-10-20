"""How the geometry source is obtained: TIGER/Line 2020 downloads.

Each frame is downloaded once and cached to data/raw as GeoParquet with its
polygons intact; the loaders return only the attribute columns the dataset
uses. Anything spatial (maps, joins) reads the cached GeoParquet directly.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

from build_dataset.ingest.geometry.geometry_feats import (
    INTERNAL_POINT_LATITUDE,
    INTERNAL_POINT_LONGITUDE,
    LAND_AREA,
)
from utils.config import RAW_NATIONAL_DIR

# TIGER/Line shapefiles for geometry.
COUNTY_GEOMETRY_2020_URL = (
    "https://www2.census.gov/geo/tiger/TIGER2020/COUNTY/tl_2020_us_county.zip"
)

# Per-state tract geometry; format with a 2-digit state FIPS, e.g. .format(state_fips="06").
TRACT_GEOMETRY_2020_URL_TEMPLATE = (
    "https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_{state_fips}_tract.zip"
)

# Cache filenames inside RAW_NATIONAL_DIR; the checksum manifest reads the
# county one from here rather than repeating the string.
COUNTY_GEOMETRY_2020_PARQUET = "county_geometry_2020.parquet"

# Per-state tract cache; format with a 2-digit state FIPS, as the URL template is.
TRACT_GEOMETRY_2020_PARQUET_TEMPLATE = "tract_geometry_2020_{state_fips}.parquet"

GEOMETRY_ATTRS = [
    "GEOID",
    "NAME",
    LAND_AREA,
    INTERNAL_POINT_LATITUDE,
    INTERNAL_POINT_LONGITUDE,
]


def load_county_geometry() -> pd.DataFrame:
    """County TIGER/Line 2020 attributes (polygons stay in the GeoParquet cache).

    Returns
    -------
    pandas.DataFrame
        One row per county: GEOID, county name, land area, and internal
        point coordinates (GEOMETRY_ATTRS), covering the full TIGER
        universe including island territories.

    Raises
    ------
    Exception
        Network or parsing errors propagated from geopandas on the
        first-time shapefile download.
    """
    RAW_NATIONAL_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_NATIONAL_DIR / COUNTY_GEOMETRY_2020_PARQUET
    if not cache.exists():
        gdf = gpd.read_file(COUNTY_GEOMETRY_2020_URL)
        gdf.to_parquet(cache)
    return pd.DataFrame(gpd.read_parquet(cache)[GEOMETRY_ATTRS])


def load_tract_geometry(state_fips: str) -> pd.DataFrame:
    """Tract TIGER/Line 2020 attributes for one state (downloaded once, then cached).

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code, e.g. "06".

    Returns
    -------
    pandas.DataFrame
        One row per tract: GEOID, name, land area, and internal point
        coordinates (GEOMETRY_ATTRS).

    Raises
    ------
    Exception
        Network or parsing errors propagated from geopandas on the
        first-time shapefile download.
    """
    RAW_NATIONAL_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_NATIONAL_DIR / TRACT_GEOMETRY_2020_PARQUET_TEMPLATE.format(
        state_fips=state_fips
    )
    if not cache.exists():
        url = TRACT_GEOMETRY_2020_URL_TEMPLATE.format(state_fips=state_fips)
        gdf = gpd.read_file(url)
        gdf.to_parquet(cache)
    return pd.DataFrame(gpd.read_parquet(cache)[GEOMETRY_ATTRS])


if __name__ == "__main__":
    print(RAW_NATIONAL_DIR)
    load_county_geometry()
