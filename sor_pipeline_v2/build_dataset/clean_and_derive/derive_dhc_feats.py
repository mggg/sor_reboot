"""Step 3: URBANSHARE from the DHC urban/rural counts.

A complete count with no margins of error, so none of the ACS sentinel or
precision machinery applies; the only check needed is the zero-denominator rule.
"""

from __future__ import annotations

import pandas as pd

from build_dataset.ingest.dhc.dhc_feats import DHC_FEATURES


def add_dhc_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive each DHC feature from its computer (which reads the prefixed
    raw columns and yields NaN for a zero denominator).

    Parameters
    ----------
    df : pandas.DataFrame
        The merged frame after numeric coercion, containing the
        `DHC_`-prefixed raw columns.

    Returns
    -------
    pandas.DataFrame
        A copy with one new column per declared DHC variable.

    Raises
    ------
    KeyError
        If a `DHC_`-prefixed input column is absent -- the step ran before
        the DHC merge.
    """
    required = {
        column
        for variable in DHC_FEATURES
        for column in variable.variable_computer.input_columns()
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise KeyError(
            f"DHC inputs absent: {missing} -- add_dhc_derived_features must "
            "run after the DHC merge."
        )
    df = df.copy()
    for variable in DHC_FEATURES:
        df[variable.var_name] = variable.variable_computer(df)
    return df
