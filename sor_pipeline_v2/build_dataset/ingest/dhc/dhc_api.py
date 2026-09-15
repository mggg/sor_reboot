"""How the DHC source is fetched: one request through the shared client."""

from __future__ import annotations

import pandas as pd

from build_dataset.ingest.census_client import DECENNIAL_DHC_URL, get_census_data
from build_dataset.ingest.dhc.dhc_vars import DHC_CODES, DHC_COLUMN_PREFIX


def fetch_dhc(for_geo: str, in_geo: str) -> pd.DataFrame:
    """The DHC urban/rural columns, one row per geographic unit, plus GEOID.

    Columns come back prefixed (see `dhc_vars.DHC_COLUMN_PREFIX`): DHC's P2
    codes share names with the PL file's P2 codes and would collide in the
    merged dataset.
    """
    df = get_census_data(DECENNIAL_DHC_URL, list(DHC_CODES), for_geo, in_geo)
    return df.rename(columns={code: DHC_COLUMN_PREFIX + code for code in DHC_CODES})
