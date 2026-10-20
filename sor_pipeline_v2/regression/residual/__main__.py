"""Out-of-fold residuals: which counties the model cannot predict.

The SHAP driver explains why the model predicted what it did; this one asks
where it was WRONG, which is the complementary question and the one that
surfaces counties worth a case study. A county whose identification
behaviour its demographics fail to anticipate is, by construction, a county
where something the matrix does not measure is happening.

Predictions are OUT OF FOLD: the sample is split into k folds and each
county is scored by a model fit on the other k-1, so no county is ever
predicted by a model that saw it. This matters more than it sounds -- a
random forest largely memorises its training rows, so in-sample residuals
(including the predicted values printed on the SHAP waterfalls) are
optimistically small and cannot be ranked against each other.

Residual = actual - predicted, so a POSITIVE residual means the model
UNDER-predicted: the county reports more of the target share than its
demographics imply. Negative means the reverse.

Two cautions when reading the ranking. Small-population counties dominate
any residual list, because a share over a handful of people swings wildly
on a few responses -- the HISPANIC count travels with every row and
`--min-hispanic` filters the printed tables on it. And folds are drawn at
random, not by state, so a held-out county's in-state neighbours may sit in
the training folds; residuals are therefore conservative for any effect
that is regionally shared.

The cross-validated R2 printed here is a fuller accuracy estimate than one
split, but the project's accuracy claims belong to the scored runs
(`regression.group_stability`), which this driver does not replace.

Run: `python -m regression.residual [--model rf|lgbm|ridge]
[--target T] [--folds K] [--seed N] [--min-hispanic N]`.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sklearn.metrics import r2_score

from build_dataset.ingest.geometry.geometry_api import load_county_geometry
from regression.shared.cross_val import DEFAULT_FOLDS, out_of_fold_predictions
from regression.shared.prepare_df import describe_sample, prepare_df_for_regression
from regression.shared.run_config import REGRESSION_TARGETS, WEIGHT_COL
from utils import config

PRINTED_ROWS = 10


def residual_table(
    model_name: str = "rf",
    target: str = next(iter(REGRESSION_TARGETS)),
    folds: int = DEFAULT_FOLDS,
    seed: int = 1,
    top_percent: float | None = None,
    bottom_percent: float | None = None,
) -> tuple[pd.DataFrame, float, str]:
    """Build the per-county residual table on the scored runs' own sample.

    Parameters
    ----------
    model_name : str
        A `make_regressor` key: "rf", "lgbm" or "ridge".
    target : str
        Which target column to model; a key of REGRESSION_TARGETS.
    folds : int
        Number of cross-validation folds.
    seed : int
        Seeds the fold shuffle and the estimators.
    top_percent, bottom_percent : float or None
        Restrict the sample to one Hispanic-population stratum, as
        `prepare_df_for_regression` defines them: `top_percent=10` keeps
        counties at or above the 90th percentile, `bottom_percent=90`
        keeps those below it, so the two partition the sample exactly.
        At most one may be set.

    Returns
    -------
    tuple of (pandas.DataFrame, float, str)
        The residual table -- GEOID, county, hispanic population, actual,
        predicted, residual, abs_residual -- sorted most under-predicted
        first; the weighted out-of-fold R2; and the sample note.

    Raises
    ------
    KeyError
        If `target` is not a declared regression target.
    """
    if target not in REGRESSION_TARGETS:
        raise KeyError(f"unknown target {target!r}; known: {list(REGRESSION_TARGETS)}")

    unfiltered_df = pd.read_parquet(config.PROCESSED_NATIONAL_COUNTIES_PARQUET)
    # The scored runs' own sample logic: full-matrix complete-case.
    prepared = prepare_df_for_regression(
        feature_groups=[],
        unfiltered_df=unfiltered_df,
        top_percent_hisp_pop=top_percent,
        bottom_percent_hisp_pop=bottom_percent,
    )
    feature_df = prepared.full_feature_df
    # The pandas stubs let a str key select a DataFrame (duplicate column
    # names are legal), but targets_df is built with one unique column per
    # target, so this is always a Series; assert to narrow it.
    target_values = prepared.targets_df[target]
    weights = prepared.hispanic_weights

    sample_note, _ = describe_sample(top_percent, bottom_percent, len(feature_df))
    print(f"{model_name}, weighted, {target}: {sample_note}, {folds} folds")
    predictions = out_of_fold_predictions(
        model_name, feature_df, target_values, weights, folds, seed
    )

    county_names = load_county_geometry().set_index("GEOID")["NAME"]
    geoids = unfiltered_df.loc[feature_df.index, "GEOID"]
    table = pd.DataFrame(
        {
            "GEOID": geoids.to_numpy(),
            "county": county_names.reindex(geoids).to_numpy(),
            WEIGHT_COL: weights.to_numpy(),
            "actual": target_values.to_numpy(),
            "predicted": predictions.to_numpy(),
        }
    )
    table["residual"] = table["actual"] - table["predicted"]
    table["abs_residual"] = table["residual"].abs()

    out_of_fold_r2 = float(
        r2_score(table["actual"], table["predicted"], sample_weight=table[WEIGHT_COL])
    )
    return table.sort_values("residual", ascending=False), out_of_fold_r2, sample_note


def _print_extremes(table: pd.DataFrame, target: str, min_hispanic: int) -> None:
    """Print the most under- and over-predicted counties passing the filter."""
    shown = table[table[WEIGHT_COL] >= min_hispanic]
    note = (
        f" (of counties with >= {min_hispanic:,} Hispanic residents)"
        if min_hispanic
        else ""
    )
    columns = ["GEOID", "county", WEIGHT_COL, "actual", "predicted", "residual"]
    for heading, rows in [
        (
            f"model UNDER-predicts {REGRESSION_TARGETS[target]}{note}",
            shown.head(PRINTED_ROWS),
        ),
        (
            f"model OVER-predicts {REGRESSION_TARGETS[target]}{note}",
            shown.tail(PRINTED_ROWS).iloc[::-1],
        ),
    ]:
        print(f"\n{heading}:")
        print(rows[columns].to_string(index=False, float_format=lambda v: f"{v:,.3f}"))


def run_residuals(
    model_name: str = "rf",
    target: str = next(iter(REGRESSION_TARGETS)),
    folds: int = DEFAULT_FOLDS,
    seed: int = 1,
    min_hispanic: int = 0,
    top_percent: float | None = None,
    bottom_percent: float | None = None,
) -> Path:
    """Write the residual table and print its extremes.

    Parameters
    ----------
    model_name, target, folds, seed
        As `residual_table`.
    min_hispanic : int
        Minimum Hispanic population for a county to appear in the PRINTED
        tables; the written CSV always holds every county of the sample.
    top_percent, bottom_percent : float or None
        Restrict the sample to one Hispanic-population stratum.

    Returns
    -------
    Path
        The CSV written.
    """
    table, out_of_fold_r2, sample_note = residual_table(
        model_name, target, folds, seed, top_percent, bottom_percent
    )
    print(
        f"\nweighted out-of-fold R2: {out_of_fold_r2:.3f} "
        f"({folds}-fold, seed {seed}) on {sample_note}"
    )
    _print_extremes(table, target, min_hispanic)

    _, stratum_suffix = describe_sample(top_percent, bottom_percent, len(table))
    output_dir = (
        config.DATA_DIR
        / "prediction"
        / "regression"
        / f"residuals_{datetime.now(UTC).astimezone().date()}_{model_name}{stratum_suffix}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"residuals_{target}_seed{seed}.csv"
    table.to_csv(output_path, index=False)
    print(f"\noutput -> {output_path}")
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m regression.residual",
        description="Out-of-fold residuals: where the model misses, by county.",
    )
    parser.add_argument("--model", choices=["rf", "lgbm", "ridge"], default="rf")
    parser.add_argument(
        "--target",
        choices=list(REGRESSION_TARGETS),
        default=next(iter(REGRESSION_TARGETS)),
    )
    parser.add_argument("--folds", type=int, default=DEFAULT_FOLDS)
    parser.add_argument("--top-percent", type=float, default=None, metavar="X")
    parser.add_argument("--bottom-percent", type=float, default=None, metavar="X")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--min-hispanic",
        type=int,
        default=0,
        metavar="N",
        help="hide counties below this Hispanic population from the printed tables",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_residuals(
        model_name=args.model,
        target=args.target,
        folds=args.folds,
        seed=args.seed,
        min_hispanic=args.min_hispanic,
        top_percent=args.top_percent,
        bottom_percent=args.bottom_percent,
    )
