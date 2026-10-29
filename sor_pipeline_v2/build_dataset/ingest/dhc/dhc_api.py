"""API for fetching DHC data from the Census Bureau's API.

Each pull is cached in RAW_NATIONAL_DIR under a name built from the
source stem and the scope's geography label, so the county pull and a
state's tract pull are separate files.
"""

from __future__ import annotations

import pandas as pd

from build_dataset.ingest.declarations.feature_utils import feature_codes
from build_dataset.ingest.dhc.dhc_feats import DHC_FEATURES
from build_dataset.ingest.fetch_and_store.census_client import (
    NATIONAL_COUNTIES,
    GeoScope,
    get_census_data,
)
from build_dataset.ingest.fetch_and_store.source_cache import (
    cache_path,
    read_cache_if_covering,
    write_canonical_cache,
)

# Demographic and Housing Characteristics file.
DECENNIAL_DHC_2020_URL = "https://api.census.gov/data/2020/dec/dhc"

# DHC's table P2 (urban/rural) shares code NAMES with the PL file's table P2
# (Hispanic by race) -- P2_002N means "urban population" here and "Hispanic
# population" there. The fetch prefixes DHC columns so the two surveys cannot
# collide in the merged dataset; the clean stage reads `DHC_COLUMN_PREFIX + code`.
DHC_COLUMN_PREFIX = "DHC_"

# Cache filename stem; `cache_path` appends the geography label and ".csv".
DHC_STEM = "dhc"


def load_dhc_features(scope: GeoScope) -> pd.DataFrame:
    """The DHC urban/rural columns, one row per geographic unit, plus GEOID.

    Columns come back prefixed (see `DHC_COLUMN_PREFIX`): DHC's P2 codes share
    names with the PL file's P2 codes and would collide in the merged dataset.

    Each scope's pull is cached in RAW_NATIONAL_DIR and served from disk
    on later builds. The cache validates itself against the
    declared features: if a newly declared DHC feature needs a column the
    cached file predates, the file is refetched and overwritten.

    Parameters
    ----------
    scope : GeoScope
        Which geographies to fetch, and which cache file holds them.

    Returns
    -------
    pandas.DataFrame
        One row per geographic unit: GEOID plus one `DHC_`-prefixed column
        per declared code, values as strings.

    Raises
    ------
    ValueError
        Propagated from the census client on a failed or inconsistent
        API response.
    """
    cache = cache_path(DHC_STEM, scope)
    cached = read_cache_if_covering(cache, feature_codes(DHC_FEATURES))
    if cached is not None:
        return cached
    return write_canonical_cache(cache, _fetch_dhc_live(scope))


def _fetch_dhc_live(scope: GeoScope) -> pd.DataFrame:
    """One live API pull, columns prefixed on return.

    Parameters
    ----------
    scope : GeoScope
        Which geographies to fetch.

    Returns
    -------
    pandas.DataFrame
        One row per geographic unit: GEOID plus the `DHC_`-prefixed
        columns, values as strings.

    Raises
    ------
    ValueError
        Propagated from the census client on a failed or inconsistent
        API response.
    """
    codes = [
        code.removeprefix(DHC_COLUMN_PREFIX) for code in feature_codes(DHC_FEATURES)
    ]
    df = get_census_data(DECENNIAL_DHC_2020_URL, codes, scope.for_geo, scope.in_geo)
    return df.rename(columns={code: DHC_COLUMN_PREFIX + code for code in codes})


if __name__ == "__main__":
    print(load_dhc_features(NATIONAL_COUNTIES).head())
