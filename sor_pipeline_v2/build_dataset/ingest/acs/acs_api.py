"""API for fetching ACS data from the Census Bureau's API.

Two vintages feed the dataset, and both flow through the same fetch:

  2016-2020   every declared estimate + its MOE twin    columns as published
  2011-2015   the growth features' prior estimates      columns suffixed
              + their MOE twins                         with PRIOR_SUFFIX

The suffix exists because every vintage publishes identical code names
(B03001_003E means "Hispanic population" in both); unsuffixed, the 2015
columns would collide with the 2020 ones in the merged dataset. The
suffixed names are pipeline inventions -- they are never request codes.

Each vintage's pull is cached in RAW_NATIONAL_DIR under a name built
from the vintage's stem and the scope's geography label, so the county
pull and a state's tract pull are separate files; a cache lacking a newly
declared column refetches itself.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from build_dataset.ingest.acs.feats import (
    ACS_FEATURES,
    PRIOR_CODES,
    PRIOR_SUFFIX,
)
from build_dataset.ingest.declarations.feature_utils import feature_codes
from build_dataset.ingest.fetch_and_store.census_client import (
    GeoScope,
    get_census_data,
)
from build_dataset.ingest.fetch_and_store.source_cache import (
    cache_path,
    read_cache_if_covering,
    write_canonical_cache,
)

# American Community Survey 5-year (2016-2020) for most features.
ACS5_2020_URL = "https://api.census.gov/data/2020/acs/acs5"

# Prior ACS 5-year (2011-2015) for growth features. The 2011-2015 vintage is the last one that can be compared to 2016-2020 without overlapping years.
ACS5_2015_URL = "https://api.census.gov/data/2015/acs/acs5"

# Cache filename stems; `cache_path` appends the geography label and ".csv".
ACS5_2020_STEM = "acs5_2020"
ACS5_2015_PRIOR_STEM = "acs5_2015_prior"


# --- Fetch lists ---------------------------------------------------------------
def estimate_codes() -> list[str]:
    """Every raw `..._###E` column the 2016-2020 fetch needs, deduplicated
    and sorted.

    The growth computers also read `_PRIOR`-suffixed columns; those are not
    Census variables -- `load_acs_prior` invents them by renaming its
    2011-2015 fetch -- so they are dropped from this request list.

    Returns
    -------
    list of str
        Sorted, deduplicated 2016-2020 estimate codes.
    """
    codes = {
        code for code in feature_codes(ACS_FEATURES) if not code.endswith(PRIOR_SUFFIX)
    }
    return sorted(codes)


def moe_twins(codes: Sequence[str]) -> list[str]:
    """The margin-of-error twin of each estimate code (`...E` -> `...M`).

    Medians carry MOEs too, so this is a blanket transform with no exceptions.

    Parameters
    ----------
    codes : sequence of str
        Estimate codes ending in "E".

    Returns
    -------
    list of str
        The same codes with the final "E" replaced by "M", in order.
    """
    return [code[:-1] + "M" for code in codes]


def all_codes() -> list[str]:
    """The full 2016-2020 request list: estimates, then their MOE twins.

    Returns
    -------
    list of str
        Every 2016-2020 estimate code followed by every MOE code.
    """
    return estimate_codes() + moe_twins(estimate_codes())


# --- Fetches -------------------------------------------------------------------
def load_acs_features(scope: GeoScope) -> pd.DataFrame:
    """All declared columns (estimates + MOEs), 2016-2020 vintage.

    Parameters
    ----------
    scope : GeoScope
        Which geographies to fetch, and which cache file holds them.

    Returns
    -------
    pandas.DataFrame
        One row per geographic unit: GEOID plus every 2016-2020 estimate
        and MOE column, values as strings.

    Raises
    ------
    ValueError
        Propagated from the census client on a failed or inconsistent
        API response.
    """
    return _fetch_acs(
        url=ACS5_2020_URL,
        request_codes=all_codes(),
        column_suffix="",
        cache_stem=ACS5_2020_STEM,
        scope=scope,
    )


def load_acs_prior(scope: GeoScope) -> pd.DataFrame:
    """The growth features' estimates + MOEs, 2011-2015 vintage, columns
    suffixed with PRIOR_SUFFIX (see the module docstring for why).

    Parameters
    ----------
    scope : GeoScope
        Which geographies to fetch, and which cache file holds them.

    Returns
    -------
    pandas.DataFrame
        One row per geographic unit: GEOID plus the prior estimate and MOE
        columns, each name carrying the `_PRIOR` suffix, values as strings.

    Raises
    ------
    ValueError
        Propagated from the census client on a failed or inconsistent
        API response.
    """
    return _fetch_acs(
        url=ACS5_2015_URL,
        request_codes=list(PRIOR_CODES) + moe_twins(PRIOR_CODES),
        column_suffix=PRIOR_SUFFIX,
        cache_stem=ACS5_2015_PRIOR_STEM,
        scope=scope,
    )


def _fetch_acs(
    url: str,
    request_codes: list[str],
    column_suffix: str,
    cache_stem: str,
    scope: GeoScope,
) -> pd.DataFrame:
    """One vintage's frame for one scope, from the cache or the API.

    Read top to bottom: try the scope's cache (only if it covers every
    currently declared column), else fetch, rename to the pipeline's
    column names, and write the cache back in canonical form.

    Parameters
    ----------
    url : str
        The vintage's Census API endpoint.
    request_codes : list of str
        Census variable codes to request.
    column_suffix : str
        Appended to every requested code to form the returned column
        names; "" leaves the published names unchanged.
    cache_stem : str
        The vintage's cache filename stem; the scope supplies the rest.
    scope : GeoScope
        Which geographies to fetch, and which cache file holds them.

    Returns
    -------
    pandas.DataFrame
        One row per geographic unit: GEOID plus one column per requested
        code (suffixed), values as strings.

    Raises
    ------
    ValueError
        Propagated from the census client on a failed or inconsistent
        API response.
    """
    cache = cache_path(cache_stem, scope)
    expected_columns = [code + column_suffix for code in request_codes]

    cached = read_cache_if_covering(cache, expected_columns)
    if cached is not None:
        return cached

    fetched = get_census_data(url, request_codes, scope.for_geo, scope.in_geo)
    fetched = fetched.rename(columns=dict(zip(request_codes, expected_columns)))
    return write_canonical_cache(cache, fetched)
