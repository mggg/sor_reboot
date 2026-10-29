"""API for fetching PL data from the Census Bureau's API.

Each table's pull is cached in RAW_NATIONAL_DIR under a name built from
the table's stem and the scope's geography label, so the county pull
and a state's tract pull are separate files; a cache lacking a newly
declared column refetches itself.
"""

import pandas as pd

from build_dataset.ingest.declarations.feature_utils import ModelVariable, feature_codes
from build_dataset.ingest.fetch_and_store.census_client import (
    GeoScope,
    get_census_data,
)
from build_dataset.ingest.fetch_and_store.source_cache import (
    cache_path,
    read_cache_if_covering,
    write_canonical_cache,
)
from build_dataset.ingest.pl.feats.hisp_pop_feats import PL_HISP_FEATURES
from build_dataset.ingest.pl.feats.total_pop_feats import PL_FEATURES

DECENNIAL_PL_2020_URL = "https://api.census.gov/data/2020/dec/pl"

# Cache filename stems; `cache_path` appends the geography label and ".csv".
PL_2020_TOTAL_STEM = "pl_2020_total"
PL_2020_HISPANIC_STEM = "pl_2020_hispanic"


def fetch_decennial_pl(scope: GeoScope) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch the P1 (total race) and P2 (Hispanic-by-race) tables.

    The aggregate features (white alone-or-in-combination, and its non-Hispanic
    twin) are built in the clean stage from these same columns: their codes are
    subsets of the per-code feature lists, so they add nothing to the fetch.

    Parameters
    ----------
    scope : GeoScope
        Which geographies to fetch, and which cache files hold them.

    Returns
    -------
    tuple of pandas.DataFrame
        Two frames: (pl_total, pl_hispanic), each with one row per geographic unit; values returned as strings.

    Raises
    ------
    ValueError
        Propagated from the census client on a failed or inconsistent
        API response.
    """
    pl_total = _fetch_pl_table(PL_FEATURES, PL_2020_TOTAL_STEM, scope)
    pl_hispanic = _fetch_pl_table(PL_HISP_FEATURES, PL_2020_HISPANIC_STEM, scope)
    return pl_total, pl_hispanic


def _fetch_pl_table(
    features: list[ModelVariable],
    cache_stem: str,
    scope: GeoScope,
) -> pd.DataFrame:
    """One PL table's frame for one scope, from the cache or the API.

    Parameters
    ----------
    features : list of ModelVariable
        The declarations whose input columns form the request list.
    cache_stem : str
        The table's cache filename stem; the scope supplies the rest.
    scope : GeoScope
        Which geographies to fetch, and which cache file holds them.

    Returns
    -------
    pandas.DataFrame
        One row per geographic unit: GEOID plus one column per requested
        code, values as strings.

    Raises
    ------
    ValueError
        Propagated from the census client on a failed or inconsistent
        API response.
    """
    cache = cache_path(cache_stem, scope)
    codes = feature_codes(features)

    cached = read_cache_if_covering(cache, codes)
    if cached is not None:
        return cached

    fetched = get_census_data(DECENNIAL_PL_2020_URL, codes, scope.for_geo, scope.in_geo)
    return write_canonical_cache(cache, fetched)
