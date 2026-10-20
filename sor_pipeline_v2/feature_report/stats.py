"""Per-feature descriptive statistics for one or more model groups.

Two sets of columns, measured on two different samples, because they
answer different questions:

  COVERAGE comes from the unfiltered frame -- how often the source
  publishes this feature at all. It has to come from there, because the
  regression sample is complete-case on the full matrix, so inside that
  sample every feature is non-null by construction and a missingness
  column would read zero for everything.

  DISTRIBUTION comes from the analysed sample, whichever the caller
  chose. Shape, spread and the correlation with the target describe the
  values a model actually sees.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

REPORTED_QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)
QUANTILE_COLUMNS = ("p5", "q1", "median", "q3", "p95")


def feature_stats(
    sample_df: pd.DataFrame,
    unfiltered_df: pd.DataFrame,
    hispanic_weights: pd.Series,
    correlation_target: pd.Series,
) -> pd.DataFrame:
    """One row per column of `sample_df`, in the order given.

    Parameters
    ----------
    sample_df : pandas.DataFrame
        The analysed values: rows are the chosen sample, columns the
        features to describe.
    unfiltered_df : pandas.DataFrame
        The frame before any row filtering, for the coverage columns.
    hispanic_weights : pandas.Series
        Hispanic population per row, aligned to `sample_df`. The models
        fit both weighted and unweighted, so the gap between a feature's
        two means says whether small-population units drive the
        unweighted picture.
    correlation_target : pandas.Series
        The one outcome every feature is correlated against, aligned to
        `sample_df`. Its `name` becomes part of the column heading, so the
        table says which outcome it measured rather than leaving "target"
        to guess.

    Returns
    -------
    pandas.DataFrame
        One row per feature; see the module docstring for the two column
        families.
    """
    rows = [
        _one_feature(
            feature_name,
            sample_df[feature_name],
            unfiltered_df[feature_name],
            hispanic_weights,
            correlation_target,
        )
        for feature_name in sample_df.columns
    ]
    return pd.DataFrame(rows)


def _as_float(value: Any) -> float:
    """A pandas reduction as a float.

    pandas-stubs types every reduction as `Scalar`, a union that includes
    `complex`, which `float()` will not take. Annotating the input as Any
    is narrower than it looks: the callers all pass a numeric reduction.
    """
    return float(value)


def _one_feature(
    feature_name: str,
    sample_values: pd.Series,
    unfiltered_values: pd.Series,
    hispanic_weights: pd.Series,
    correlation_target: pd.Series,
) -> dict[str, object]:
    """One feature's row. See `feature_stats` for the column meanings."""
    non_null_values = sample_values.dropna().to_numpy(dtype=float)
    quantile_values = (
        np.quantile(non_null_values, REPORTED_QUANTILES)
        if non_null_values.size
        else np.full(len(REPORTED_QUANTILES), np.nan)
    )
    mean = float(non_null_values.mean()) if non_null_values.size else np.nan
    sd = float(non_null_values.std(ddof=1)) if non_null_values.size > 1 else np.nan
    minimum = float(non_null_values.min()) if non_null_values.size else np.nan
    maximum = float(non_null_values.max()) if non_null_values.size else np.nan

    row: dict[str, object] = {
        "feature": feature_name,
        "n_rows_in_file": len(unfiltered_values),
        "n_rows_with_a_value": int(unfiltered_values.notna().sum()),
        "pct_of_file_missing": round(
            100 * _as_float(unfiltered_values.isna().mean()), 2
        ),
        "n_rows_in_this_report": int(non_null_values.size),
        "mean": mean,
        "weighted_mean": _weighted_mean(sample_values, hispanic_weights),
        "sd": sd,
        "sd_over_mean": (
            sd / mean if non_null_values.size and minimum >= 0 and mean else None
        ),
        "min": minimum,
    }
    row.update(
        dict(zip(QUANTILE_COLUMNS, (float(q) for q in quantile_values), strict=True))
    )
    row.update(
        {
            "max": maximum,
            "range": maximum - minimum,
            "iqr": float(quantile_values[3] - quantile_values[1]),
            "pct_zero": (
                round(100 * float((non_null_values == 0).mean()), 2)
                if non_null_values.size
                else np.nan
            ),
            "pct_exactly_1": (
                round(100 * float((non_null_values == 1).mean()), 2)
                if non_null_values.size and 0 <= minimum and maximum <= 1
                else None
            ),
            "skew": (
                _as_float(sample_values.skew()) if non_null_values.size > 2 else np.nan
            ),
            "n_unique": int(sample_values.nunique()),
            f"spearman_with_{correlation_target.name}": _spearman(
                sample_values, correlation_target
            ),
        }
    )
    return row


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Mean weighted by `weights`, over rows where both are non_null_values."""
    both_present = values.notna() & weights.notna()
    weight_total = _as_float(weights[both_present].sum())
    if not weight_total:
        return np.nan
    return (
        _as_float((values[both_present] * weights[both_present]).sum()) / weight_total
    )


def _spearman(values: pd.Series, target: pd.Series) -> float:
    """Spearman correlation with the target, over rows where both exist."""
    if values.nunique() < 2:
        return np.nan
    return _as_float(values.corr(target, method="spearman"))
