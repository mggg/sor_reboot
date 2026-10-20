"""Step 0 of cleaning and transforming: strings -> numbers.

The census client returns every value as a string (fidelity to the API, and
what keeps GEOIDs zero-padded). Turn everything except for GEOID and NAME into a numeric column,
coercing any non-numeric string to NaN.
"""

from __future__ import annotations

import pandas as pd

STRING_COLS = ("GEOID", "NAME")


def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce every non-identifier column to numeric.

    Parameters
    ----------
    df : pandas.DataFrame
        The assembled ingest frame, every value a string as the sources
        delivered it.

    Returns
    -------
    pandas.DataFrame
        A copy with every column except STRING_COLS (GEOID, NAME) numeric;
        any non-numeric string becomes NaN.
    """
    df = df.copy()
    value_cols = [c for c in df.columns if c not in STRING_COLS]
    df[value_cols] = df[value_cols].apply(pd.to_numeric, errors="coerce")
    return df
