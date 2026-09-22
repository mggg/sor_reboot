"""Step 4 of cleaning and transforming: DENSITY from the TIGER attributes.

INTPTLAT/INTPTLON need no work here -- coercion already made them floats (the
TIGER `+32.53` strings parse directly).

Depends on step 1: TOTALPOP is born in the PL renames. Zero land area yields
NaN density rather than dropping the row -- clean never deletes units (at
county level no unit has zero land, so nothing hits this).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_geometry_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive DENSITY; requires TOTALPOP (step 1) and ALAND (ingest).

    Other geometry features (INTPTLAT, INTPTLON) are already present and don't need derivation.
    """
    if "TOTALPOP" not in df.columns:
        raise KeyError(
            "TOTALPOP absent -- add_geometry_derived_features must run after the PL "
            "step (clean.pl.add_targets), which creates it."
        )
    df = df.copy()
    df["DENSITY"] = df["TOTALPOP"] / df["ALAND"].replace(0, np.nan)
    return df
