"""Step 2: the ACS features, each computed by its declared variable_computer.

Order of operations matters and is fixed here: sentinels -> NaN first, so the
computers' sums and shares never mistake a sentinel for a real value (their
NaN discipline -- skipna=False sums, NaN on zero denominators -- handles the
rest).
"""

from __future__ import annotations

import pandas as pd

from build_dataset.ingest.declarations.feature_utils import ModelVariable

# Values the API substitutes for a real number. Each means the estimate or
# margin could not be produced; all of them must become NaN before arithmetic,
# because they are large and negative -- they do not look like missing data,
# they look like plausible arithmetic.
SENTINELS: dict[int, str] = {
    -666666666: "estimate cannot be computed (too few sample cases)",
    -999999999: "estimate not available",
    -555555555: "margin cannot be computed, or falls in the lowest/highest interval",
    -222222222: "estimate controlled -- margin not appropriate",
    -333333333: "margin not appropriate for this median",
    -888888888: "not applicable",
}


def nullify_sentinels(df: pd.DataFrame) -> pd.DataFrame:
    """Replace every ACS sentinel value with NaN, across all numeric columns.

    Parameters
    ----------
    df : pandas.DataFrame
        The merged frame after numeric coercion; sentinel values sit in its
        numeric columns as the large negative numbers in SENTINELS.

    Returns
    -------
    pandas.DataFrame
        A copy with every sentinel occurrence replaced by NaN; non-numeric
        columns untouched.
    """
    df = df.copy()
    numeric = df.select_dtypes("number").columns
    block = df[numeric]
    df[numeric] = block.mask(block.isin(list(SENTINELS)))
    return df


def add_acs_features(
    df: pd.DataFrame, model_variables: list[ModelVariable]
) -> pd.DataFrame:
    """Derive every ACS feature (growth features included) from its computer.

    Parameters
    ----------
    df : pandas.DataFrame
        The merged frame after numeric coercion, containing every raw ACS
        column the declared computers read (current estimates and the
        `_PRIOR`-suffixed prior-vintage columns).
    model_variables : list of ModelVariable
        The ACS declarations to compute, in list order.

    Returns
    -------
    pandas.DataFrame
        A copy with sentinels nullified and one new column per declared
        variable.

    Raises
    ------
    KeyError
        If a raw column a computer reads is absent -- the fetch and the
        feats declarations have drifted apart.
    """
    df = df.copy()
    required = {
        column
        for variable in model_variables
        for column in variable.variable_computer.input_columns()
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise KeyError(
            f"{len(missing)} required ACS column(s) absent, first few: "
            f"{missing[:5]}. The fetch and the feats declarations have drifted "
            "apart -- re-run ingest with the current acs_api fetch lists."
        )

    df = nullify_sentinels(df)

    # One concat, not ~90 sequential inserts: every ACS computer reads only
    # fetched columns, never another ACS variable, so all outputs can be
    # computed against the same frame and joined at once. Inserting one
    # column at a time fragments the frame's memory blocks (pandas
    # PerformanceWarning) and is markedly slower.
    computed = pd.concat(
        {
            variable.var_name: variable.variable_computer(df)
            for variable in model_variables
        },
        axis=1,
    )
    return pd.concat([df, computed], axis=1)


def main_acs_clean_and_transform(
    df: pd.DataFrame, model_variables: list[ModelVariable]
) -> pd.DataFrame:
    """The full ACS step: sentinels, then every declared computer.

    Parameters
    ----------
    df : pandas.DataFrame
        The merged frame after numeric coercion.
    model_variables : list of ModelVariable
        The ACS declarations to compute.

    Returns
    -------
    pandas.DataFrame
        The frame with every declared ACS variable added.

    Raises
    ------
    KeyError
        Propagated from `add_acs_features` when a required raw column is
        absent.
    """
    return add_acs_features(df, model_variables)
