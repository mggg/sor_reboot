"""API for fetching DHC data from the Census Bureau's API."""

from __future__ import annotations

import pandas as pd

from build_dataset.ingest.census_client import DECENNIAL_DHC_2020_URL, get_census_data
from build_dataset.ingest.dhc.dhc_feats import DHC_FEATURES
from build_dataset.ingest.feature_utils import feature_codes

# DHC's table P2 (urban/rural) shares code NAMES with the PL file's table P2
# (Hispanic by race) -- P2_002N means "urban population" here and "Hispanic
# population" there. The fetch prefixes DHC columns so the two surveys cannot
# collide in the merged dataset; the clean stage reads `DHC_COLUMN_PREFIX + code`.
DHC_COLUMN_PREFIX = "DHC_"


def fetch_dhc(for_geo: str, in_geo: str) -> pd.DataFrame:
    """The DHC urban/rural columns, one row per geographic unit, plus GEOID.

    Columns come back prefixed (see `DHC_COLUMN_PREFIX`): DHC's P2 codes share
    names with the PL file's P2 codes and would collide in the merged dataset.
    """
    codes = feature_codes(DHC_FEATURES)
    df = get_census_data(DECENNIAL_DHC_2020_URL, codes, for_geo, in_geo)
    return df.rename(columns={code: DHC_COLUMN_PREFIX + code for code in codes})
