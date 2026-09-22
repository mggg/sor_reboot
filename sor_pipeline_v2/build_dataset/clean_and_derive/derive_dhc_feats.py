"""Step 3: URBANSHARE from the DHC urban/rural counts.

A complete count with no margins of error, so none of the ACS sentinel or
precision machinery applies; the only check needed is the zero-denominator rule.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from build_dataset.ingest.dhc.dhc_api import DHC_COLUMN_PREFIX
from build_dataset.ingest.dhc.dhc_feats import DHC_FEATURES


def add_dhc_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive each DHC feature from its prefixed raw columns."""
    df = df.copy()
    for feature in DHC_FEATURES:
        numerator = feature.numerator_codes[0]
        denominator = feature.denominator_codes[0]
        name = feature.var_name
        # Zero denominator means the share is undefined, not zero.
        den = df[DHC_COLUMN_PREFIX + denominator].replace(0, np.nan)
        df[name] = df[DHC_COLUMN_PREFIX + numerator] / den
    return df
