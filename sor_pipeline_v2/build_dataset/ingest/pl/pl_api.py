"""API for fetching PL data from the Census Bureau's API."""

import pandas as pd

from build_dataset.ingest.census_client import (
    DECENNIAL_PL_2020_URL,
    get_census_data,
)
from build_dataset.ingest.feature_utils import feature_codes
from build_dataset.ingest.pl.hisp_pop_feats import PL_HISP_FEATURES
from build_dataset.ingest.pl.total_pop_feats import PL_FEATURES


def fetch_decennial_pl(for_geo: str, in_geo: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch the P1 (total race) and P2 (Hispanic-by-race) tables.

    The aggregate features (white alone-or-in-combination, and its non-Hispanic
    twin) are built in the clean stage from these same columns: their codes are
    subsets of the per-code feature lists, so they add nothing to the fetch.

    Parameters
    ----------
    for_geo : str
        The `for=` clause, e.g. "county:*" or "tract:*".
    in_geo : str
        The `in=` clause, e.g. "state:*" or "state:06".

    Returns
    -------
    tuple of pandas.DataFrame
        Two frames: (pl_total, pl_hispanic), each with one row per geographic unit; values returned as strings.
    """

    print("Fetching 2020 Decennial PL data...")
    pl_total = get_census_data(
        DECENNIAL_PL_2020_URL, feature_codes(PL_FEATURES), for_geo, in_geo
    )
    pl_hispanic = get_census_data(
        DECENNIAL_PL_2020_URL, feature_codes(PL_HISP_FEATURES), for_geo, in_geo
    )
    print("Done fetching 2020 Decennial PL data.")
    return pl_total, pl_hispanic
