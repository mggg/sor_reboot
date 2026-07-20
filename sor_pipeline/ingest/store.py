"""Persist and reload pipeline artifacts across the data/ tree.

Thin helpers over parquet/json so each stage reads from and writes to a known
location (data/raw -> data/interim -> data/processed) instead of dumping files
into the working directory the way the notebooks do.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import geopandas as gpd


def save(df: pd.DataFrame | gpd.GeoDataFrame, path: Path):
    """Write a (Geo)DataFrame to parquet, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)


def load(path: Path) -> pd.DataFrame | gpd.GeoDataFrame:
    """Read a (Geo)DataFrame back from parquet.

    Tries GeoParquet first so geometry typing + CRS survive the round-trip (pandas
    alone would hand geometry back as raw WKB bytes). Falls back to a plain
    DataFrame for tables that were written without any geometry column.
    """
    if path.suffix != ".parquet":
        raise NotImplementedError("Only parquet files are supported.")
    try:
        return gpd.read_parquet(path)
    except Exception:
        return pd.read_parquet(path)
