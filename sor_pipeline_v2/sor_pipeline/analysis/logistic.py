"""Univariate logistic regressions: each covariate alone vs. a binary race-choice target.

Migrated from `3hispaniccleanjune` section 6 (univariate logistic regressions). The
notebook fit one single-predictor `statsmodels` Logit per (dominant-race indicator,
covariate) and printed the full summaries. Here we fit the same models and expose them
two ways: a tidy table of the key stats (for analysis/saving, like `correlations.py`),
and the verbatim statsmodels summaries as text (notebook parity).

Count covariates (VARS_LOG) are log-transformed on strictly positive rows; the rest
(VARS_NO_LOG) are used as-is. Each model includes an intercept.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from sor_pipeline.utils.config import VARS_LOG, VARS_NO_LOG

# The three binary dominant-race indicators (one-hots from features.add_dominant_race_choice).
RACE_TARGETS = ["Most_SOR", "Most_White_SOR", "Most_White"]


def _design(df, target: str, variable: str, log: bool):
    """Build (y, X) for one single-predictor model; log-transform positive rows if asked."""
    if log:
        subset = df[df[variable] > 0]  # keep strictly positive so the log is defined
        x = np.log(subset[variable])
    else:
        subset = df[df[variable].notna()]
        x = subset[variable]
    y = subset[target].astype(int)  # binary response
    X = sm.add_constant(x)  # add intercept term
    return y, X


def _fit(df, target: str, variable: str, log: bool):
    """Fit one Logit; return (result_or_None, n). None when the fit fails to converge."""
    y, X = _design(df, target, variable, log)
    try:
        return sm.Logit(y, X).fit(disp=False), len(y)
    except Exception:
        return None, len(y)


def _iter_models(targets, vars_log, vars_no_log):
    """Yield (target, variable, log) for every (target, covariate) pair, log group first."""
    for target in targets:
        for variable in vars_log:
            yield target, variable, True
        for variable in vars_no_log:
            yield target, variable, False


def _defaults(targets, vars_log, vars_no_log):
    return (
        targets if targets is not None else RACE_TARGETS,
        vars_log if vars_log is not None else VARS_LOG,
        vars_no_log if vars_no_log is not None else VARS_NO_LOG,
    )


def univariate_logistic(
    df,
    targets: list[str] | None = None,
    vars_log: list[str] | None = None,
    vars_no_log: list[str] | None = None,
) -> pd.DataFrame:
    """Fit one logistic regression per (target, covariate) pair; return a tidy table.

    One row per (target, covariate) with coef / std err / z / p-value / pseudo-R² / n,
    sorted by target then ascending p-value (most significant first). A fit that fails
    to converge records NaNs rather than killing the run.
    """
    targets, vars_log, vars_no_log = _defaults(targets, vars_log, vars_no_log)

    rows = []
    for target, variable, log in _iter_models(targets, vars_log, vars_no_log):
        result, n = _fit(df, target, variable, log)
        row = {
            "target": target,
            "covariate": variable,
            "transform": "log" if log else "none",
            "n": n,
        }
        if result is not None:
            row.update(
                {
                    "coef": result.params[variable],
                    "std_err": result.bse[variable],
                    "z": result.tvalues[variable],
                    "p_value": result.pvalues[variable],
                    "pseudo_r2": result.prsquared,
                }
            )
        else:
            row.update(
                {
                    "coef": np.nan,
                    "std_err": np.nan,
                    "z": np.nan,
                    "p_value": np.nan,
                    "pseudo_r2": np.nan,
                }
            )
        rows.append(row)

    table = pd.DataFrame(rows)
    return table.sort_values(["target", "p_value"]).reset_index(drop=True)


def coefficient_matrix(table: pd.DataFrame) -> pd.DataFrame:
    """Pivot the tidy table into a covariate × target matrix of coefficients (for display)."""
    return table.pivot(index="covariate", columns="target", values="coef")


def summary_report(
    df,
    targets: list[str] | None = None,
    vars_log: list[str] | None = None,
    vars_no_log: list[str] | None = None,
) -> str:
    """Full statsmodels `.summary()` for every model, concatenated as text (notebook parity)."""
    targets, vars_log, vars_no_log = _defaults(targets, vars_log, vars_no_log)

    blocks = []
    current_target = None
    for target, variable, log in _iter_models(targets, vars_log, vars_no_log):
        if target != current_target:
            blocks.append(f"\n{'=' * 30}\n--- {target} ---\n{'=' * 30}")
            current_target = target
        result, _ = _fit(df, target, variable, log)
        label = f"{variable} (log)" if log else variable
        blocks.append(label)
        blocks.append(
            str(result.summary()) if result is not None else "  [fit did not converge]"
        )
    return "\n".join(blocks)
