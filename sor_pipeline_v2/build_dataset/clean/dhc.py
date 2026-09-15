"""Step 3: URBANSHARE from the DHC urban/rural counts.

A complete count with no margins of error, so none of the ACS sentinel or
precision machinery applies; the only care needed is the zero-denominator rule.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from build_dataset.ingest.dhc.dhc_vars import DHC_COLUMN_PREFIX, DHC_FEATURES


def add_dhc_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive each DHC feature from its prefixed raw columns."""
    df = df.copy()
    for name, numerator, denominator, _meaning in DHC_FEATURES:
        den = df[DHC_COLUMN_PREFIX + denominator].replace(0, np.nan)
        df[name] = df[DHC_COLUMN_PREFIX + numerator] / den
    return df
