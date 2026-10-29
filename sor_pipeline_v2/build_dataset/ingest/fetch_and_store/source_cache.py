"""The cache halves shared by the census source APIs, at every scope.

Each api keeps its own linear fetch flow and calls these at the top and
bottom; only the three invariants live here, exactly once:

  - reads are dtype=str, so a cached build is identical to a fetched one
    (the census client returns every value as a string and raw.parquet
    stores them that way; a bare read_csv would re-type numerics);
  - writes are canonical -- rows sorted by GEOID, fetch-list column
    order -- so identical data always produces an identical (hashable)
    file;
  - names are built from a stem and a scope, so one source's caches for
    different geographies cannot overwrite each other.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from build_dataset.ingest.fetch_and_store.census_client import GeoScope
from utils.config import RAW_NATIONAL_DIR


def cache_path(stem: str, scope: GeoScope) -> Path:
    """Where one source's cache for one scope lives.

    Parameters
    ----------
    stem : str
        The source's filename stem, e.g. "pl_2020_total".
    scope : GeoScope
        The scope the file holds; its `geography_label` is what
        distinguishes `pl_2020_total_national_counties.csv` from
        `pl_2020_total_tracts_06.csv`.

    Returns
    -------
    Path
        The cache CSV's location; parent directories are created.
    """
    RAW_NATIONAL_DIR.mkdir(parents=True, exist_ok=True)
    return RAW_NATIONAL_DIR / f"{stem}_{scope.geography_label}.csv"


def read_cache_if_covering(
    cache: Path, expected_columns: Iterable[str]
) -> pd.DataFrame | None:
    """The cached frame, or None if absent or missing a declared column.

    A cache that predates newly declared features announces itself and
    returns None so the caller refetches and overwrites.

    Parameters
    ----------
    cache : Path
        The cache CSV's location on disk.
    expected_columns : iterable of str
        Every column the current declarations require; StrEnum members are
        accepted (they compare as their string values).

    Returns
    -------
    pandas.DataFrame or None
        The cached frame with every value as a string, or None when the
        file does not exist or lacks any expected column.
    """
    if not cache.exists():
        return None
    cached = pd.read_csv(cache, dtype=str)
    missing = sorted(
        str(column) for column in set(expected_columns) - set(cached.columns)
    )
    if missing:
        print(f"{cache.name} lacks newly declared column(s) {missing}; refetching.")
        return None
    return cached


def write_canonical_cache(cache: Path, frame: pd.DataFrame) -> pd.DataFrame:
    """Write the frame in canonical form and return it as written.

    Parameters
    ----------
    cache : Path
        Destination CSV path; overwritten if present.
    frame : pandas.DataFrame
        The freshly fetched frame; must contain a GEOID column.

    Returns
    -------
    pandas.DataFrame
        The frame as written: rows sorted by GEOID, index reset.

    Raises
    ------
    KeyError
        If the frame has no GEOID column to sort by.
    """
    frame = frame.sort_values("GEOID").reset_index(drop=True)
    frame.to_csv(cache, index=False)
    return frame
