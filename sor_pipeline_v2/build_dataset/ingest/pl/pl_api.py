import pandas as pd

from build_dataset.ingest.census_client import (
    DECENNIAL_PL_URL,
    get_census_data,
)
from build_dataset.ingest.pl.pl_vars import VARS_PL_HISPANIC, VARS_PL_TOTAL


def fetch_decennial_pl(for_geo: str, in_geo: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch the P1 (total race) and P2 (Hispanic-by-race) tables.

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
    pl_total = get_census_data(DECENNIAL_PL_URL, VARS_PL_TOTAL, for_geo, in_geo)
    pl_hispanic = get_census_data(DECENNIAL_PL_URL, VARS_PL_HISPANIC, for_geo, in_geo)
    print("Done fetching 2020 Decennial PL data.")
    return pl_total, pl_hispanic
