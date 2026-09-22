"""API for fetching ACS data from the Census Bureau's API."""

from __future__ import annotations

import pandas as pd

from build_dataset.ingest.acs.feats import (
    ACS_FEATURES,
    PRIOR_CODES,
    PRIOR_SUFFIX,
)
from build_dataset.ingest.census_client import (
    ACS5_2015_URL,
    ACS5_2020_URL,
    get_census_data,
)
from build_dataset.ingest.feature_utils import feature_codes


# --- Fetch lists ---------------------------------------------------------------
def estimate_codes() -> list[str]:
    """Every raw `..._###E` column the fetch needs, deduplicated and sorted.

    Feature numerators and denominators. Sorted so the request order is stable across runs (which keeps the
    on-disk column order stable, which keeps diffs readable).
    """
    codes = set(feature_codes(ACS_FEATURES))
    return sorted(codes)


def moe_codes() -> list[str]:
    """The margin-of-error twin of every estimate column (`...E` -> `...M`).

    Medians carry MOEs too, so this is a blanket transform with no exceptions.
    """
    return [code[:-1] + "M" for code in estimate_codes()]


def all_codes(include_moe: bool = True) -> list[str]:
    """Full request list: estimates, optionally followed by their margins."""
    codes = estimate_codes()
    return codes + moe_codes() if include_moe else codes


# --- Fetches -------------------------------------------------------------------
def fetch_acs_features(for_geo: str, in_geo: str) -> pd.DataFrame:
    """All declared columns (estimates + MOEs), 2016-2020 vintage."""
    return get_census_data(ACS5_2020_URL, all_codes(), for_geo, in_geo)


def fetch_acs_prior(for_geo: str, in_geo: str) -> pd.DataFrame:
    """The growth-feature codes from the 2011-2015 vintage.

    Columns come back suffixed (see `PRIOR_SUFFIX`): the prior vintage publishes
    the same code names as 2016-2020, and unsuffixed they would collide with
    `fetch_acs_features` columns in the merged dataset.
    """
    df = get_census_data(ACS5_2015_URL, list(PRIOR_CODES), for_geo, in_geo)
    return df.rename(columns={code: code + PRIOR_SUFFIX for code in PRIOR_CODES})
