"""Pearson correlations of the race-to-Hispanic ratios against demographic covariates.

Migrated from the correlation loop in `3hispaniccleanjune` cell 5. Unlike the
notebook (which printed inline), these functions *return* the correlation values
so the driver decides how to display or save them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from sor_pipeline.utils.config import VARS_LOG, VARS_NO_LOG

# The three race-within-Hispanic ratio targets produced by clean.features.add_ratios.
RATIO_COLUMNS = [
    "Hisp SOR Alone_to_Hisp_Ratio",
    "Hisp White Alone_to_Hisp_Ratio",
    "Hisp White SOR_to_Hisp_Ratio",
]

# Covariates correlated against each ratio (the notebook's list == VARS_LOG + VARS_NO_LOG,
# used here on their raw scale, not log-transformed).
DEFAULT_COVARIATES = VARS_LOG + VARS_NO_LOG


def correlation_series(
    df, target: str, covariates: list[str] | None = None
) -> pd.Series:
    """Pearson correlation of each covariate with one ratio target.

    Rows with inf/NaN in the target or any covariate are dropped first (matching the
    notebook). Returns a Series indexed by covariate, sorted by descending |corr|.

    Parameters
    ----------
    df : DataFrame
        Must contain ``target`` and every column in ``covariates``.
    target : str
        A race-to-Hispanic ratio column (see ``RATIO_COLUMNS``).
    covariates : list of str, optional
        Columns to correlate against ``target``; defaults to ``DEFAULT_COVARIATES``.
    """
    covariates = list(covariates) if covariates is not None else DEFAULT_COVARIATES
    cols = [target] + covariates
    clean = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    corr = clean.corr(method="pearson")[target].drop(target)
    return corr.reindex(corr.abs().sort_values(ascending=False).index)


def correlation_table(df, covariates: list[str] | None = None) -> pd.DataFrame:
    """Correlation series for all three ratio targets, as one DataFrame (ratios = columns)."""
    return pd.DataFrame(
        {ratio: correlation_series(df, ratio, covariates) for ratio in RATIO_COLUMNS}
    )
