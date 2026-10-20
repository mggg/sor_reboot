"""Step 4: the geometry features, each computed by its declared computer.

INTPTLAT/INTPTLON pass through (coercion already made the TIGER `+32.53`
strings floats). DENSITY depends on step 1: TOTALPOP is born in the PL step.
Zero land area yields NaN density rather than dropping the row -- the derive
stage never deletes units (at county level no unit has zero land, so nothing
hits this).
"""

from __future__ import annotations

import pandas as pd

from build_dataset.ingest.geometry.geometry_feats import GEOMETRY_FEATURES


def add_geometry_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the geometry features from their computers.

    Parameters
    ----------
    df : pandas.DataFrame
        The merged frame after the PL step, containing the TIGER attribute
        columns and TOTALPOP (DENSITY's numerator).

    Returns
    -------
    pandas.DataFrame
        A copy with one new column per declared geometry variable.

    Raises
    ------
    KeyError
        If an input column is absent -- the step ran before the geometry
        merge or before the PL step that creates TOTALPOP.
    """
    required = {
        column
        for variable in GEOMETRY_FEATURES
        for column in variable.variable_computer.input_columns()
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise KeyError(
            f"geometry inputs absent: {missing} -- add_geometry_derived_features "
            "must run after the geometry merge and the PL step (which creates "
            "TOTALPOP)."
        )
    df = df.copy()
    for variable in GEOMETRY_FEATURES:
        df[variable.var_name] = variable.variable_computer(df)
    return df
