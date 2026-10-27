"""Substitution test: is a feature load-bearing, or just the one that won?

Tree models split greedily, so among correlated features whichever one wins
the early splits collects almost all the attribution and its partners look
unimportant -- their information was already spent. A high SHAP rank can
therefore mean "this feature is necessary" or merely "this feature got
there first," and the two are indistinguishable from the ranking alone.

This driver separates them by removing the feature and refitting:

  * which features RISE to take its place (its correlated partners, if the
    signal is redundant; nothing in particular, if it was unique), and
  * what the removal COSTS in out-of-fold R2 -- near zero means the model
    never needed that column.

Run: `python -m regression.substitution [--feature NAME] [--model rf|lgbm]
[--target T] [--top-percent X | --bottom-percent X]`.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold

from build_dataset.feature_manifest import SlugGroupName, group_features
from regression.shared.cross_val import DEFAULT_FOLDS, out_of_fold_predictions
from regression.shared.fit import fit_weighted, make_regressor
from regression.shared.prepare_df import describe_sample, prepare_df_for_regression
from regression.shared.run_config import REGRESSION_TARGETS
from regression.shared.shap_figures import plot_waterfall
from regression.shared.unit_labels import load_unit_names, unit_label
from utils import config

# Partners this correlated with the tested feature are reported as its cluster.
CLUSTER_CORRELATION = 0.35
REPORTED_ROWS = 8


def mean_abs_shap(
    model_name: str, seed: int, X: pd.DataFrame, y: pd.Series, w: pd.Series
) -> pd.Series:
    """Mean |SHAP| per feature for a model fit on all of `X`.

    Fitting in-sample is deliberate here: the question is which columns the
    trees actually split on, not how well the fit generalises (the R2 half
    of the test is out-of-fold and answers that).

    Parameters
    ----------
    model_name : str
        A `make_regressor` key; a tree model (SHAP TreeExplainer).
    seed : int
        Seeds the estimator.
    X, y, w : pandas.DataFrame, pandas.Series, pandas.Series
        Feature matrix, target and sample weights, aligned.

    Returns
    -------
    pandas.Series
        Mean absolute SHAP value per feature, descending.
    """
    model = make_regressor(model_name, seed)
    fit_weighted(model, X, y, w.to_numpy())
    explanation = shap.TreeExplainer(model)(X)
    # asarray: shap's stubs do not type Explanation.values as an array, so
    # .ndim is unknown to the checker; at runtime it is an ndarray.
    values = np.asarray(explanation.values)
    if values.ndim == 3:  # some explainers add an output axis
        values = values[..., 0]
    return pd.Series(np.abs(values).mean(axis=0), index=X.columns).sort_values(
        ascending=False
    )


def _explain_county_out_of_fold(
    matrix: pd.DataFrame,
    y: pd.Series,
    w: pd.Series,
    row: int,
    model_name: str,
    seed: int,
    folds: int,
):
    """One county's held-out SHAP explanation, from the fold that excluded it.

    Parameters
    ----------
    matrix : pandas.DataFrame
        The feature matrix to fit on.
    y, w : pandas.Series
        Target and sample weights, aligned to `matrix`.
    row : int
        Positional index of the county within `matrix`.
    model_name : str
        A `make_regressor` key; a tree model.
    seed : int
        Seeds the folds and the estimator.
    folds : int
        Number of cross-validation folds.

    Returns
    -------
    tuple
        (single-row shap.Explanation, that county's prediction).

    Raises
    ------
    RuntimeError
        If the county never lands in a test fold, which a partition makes
        impossible -- so this firing means the splitter changed.
    """
    for train_rows, test_rows in KFold(
        n_splits=folds, shuffle=True, random_state=seed
    ).split(matrix):
        if row not in set(test_rows):
            continue
        model = make_regressor(model_name, seed)
        fit_weighted(
            model,
            matrix.iloc[train_rows],
            y.iloc[train_rows],
            w.iloc[train_rows].to_numpy(),
        )
        held_out = matrix.iloc[test_rows]
        explanation = shap.TreeExplainer(model)(held_out)
        if np.asarray(explanation.values).ndim == 3:
            explanation = explanation[..., 0]
        local = int(np.where(test_rows == row)[0][0])
        prediction = float(np.asarray(model.predict(held_out))[local])
        return explanation[local], prediction
    raise RuntimeError(f"row {row} was never held out; the splitter changed")


def plot_county_substitution(
    X: pd.DataFrame,
    y: pd.Series,
    w: pd.Series,
    geoids: pd.Series,
    county: str,
    removed: str,
    model_name: str,
    target: str,
    seed: int,
    folds: int,
    sample_note: str,
    output_dir: Path,
) -> list[Path]:
    """Write before/after waterfalls for one county, using the project's
    existing waterfall renderer so the pair is directly comparable.

    Returns
    -------
    list of Path
        The two PNGs written, before then after.
    """
    # numpy, not Index.get_loc/get_indexer: both have awkward union return
    # types (slice, mask, Index-only argument). Position in `geoids` is
    # position in `X` -- they share an index by construction.
    positions = np.flatnonzero(geoids.to_numpy() == county)
    if positions.size == 0:
        raise KeyError(f"{county} is not in this sample")
    row = int(positions[0])
    county_names = load_unit_names("national_counties", geoids)
    title = unit_label(county, county_names)

    written = []
    for label, matrix in (("with", X), ("without", X.drop(columns=[removed]))):
        explanation, prediction = _explain_county_out_of_fold(
            matrix, y, w, row, model_name, seed, folds
        )
        path = output_dir / f"waterfall_{county}_{label}-{removed}.png"
        plot_waterfall(
            explanation,
            county_title=f"{title} — {label.upper()} {removed}",
            actual=float(y.iloc[row]),
            predicted=prediction,
            target_label=REGRESSION_TARGETS[target],
            model_note=f"{model_name} (seed {seed}), weighted",
            sample_note=sample_note,
            output_path=path,
        )
        written.append(path)
    return written


def substitution_test(
    feature: str | None = None,
    model_name: str = "rf",
    target: str = next(iter(REGRESSION_TARGETS)),
    seed: int = 1,
    folds: int = DEFAULT_FOLDS,
    top_percent: float | None = None,
    bottom_percent: float | None = None,
    exclude_groups: list[SlugGroupName] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Remove one feature, refit, and report what replaced it and what it cost.

    Parameters
    ----------
    feature : str or None
        The feature to remove; None tests whichever ranks first by mean
        |SHAP| in the full model.
    model_name : str
        A `make_regressor` key; a tree model.
    target : str
        A REGRESSION_TARGETS key.
    seed : int
        Seeds the estimators and the folds.
    folds : int
        Cross-validation folds for the R2 half.
    top_percent, bottom_percent : float or None
        Restrict to one Hispanic-population stratum.

    Returns
    -------
    tuple of (pandas.DataFrame, dict)
        A per-feature comparison table (rank and mean |SHAP| before and
        after, correlation with the tested feature, correlation with the
        target), and a summary dict of the R2 cost.

    Raises
    ------
    KeyError
        If `feature` is not a column of the model matrix.
    """
    unfiltered_df = pd.read_parquet(config.PROCESSED_NATIONAL_COUNTIES_PARQUET)
    prepared = prepare_df_for_regression(
        feature_groups=[],
        unfiltered_df=unfiltered_df,
        top_percent_hisp_pop=top_percent,
        bottom_percent_hisp_pop=bottom_percent,
    )
    X = prepared.full_feature_df
    if exclude_groups:
        gone = {c for g in exclude_groups for c in group_features([g])}
        kept = [c for c in X.columns if c not in gone]
        ablated = X[kept]
        X = ablated
    y = prepared.targets_df[target]
    w = prepared.hispanic_weights

    before = mean_abs_shap(model_name, seed, X, y, w)
    if feature is None:
        feature = str(before.index[0])
    if feature not in X.columns:
        raise KeyError(
            f"{feature!r} is not a model feature; e.g. {list(X.columns[:3])}"
        )

    X_without = X.drop(columns=[feature])
    after = mean_abs_shap(model_name, seed, X_without, y, w)

    r2_before = r2_score(
        y, out_of_fold_predictions(model_name, X, y, w, folds, seed), sample_weight=w
    )
    r2_after = r2_score(
        y,
        out_of_fold_predictions(model_name, X_without, y, w, folds, seed),
        sample_weight=w,
    )

    comparison = pd.DataFrame(
        {
            "shap_before": before,
            "rank_before": before.rank(ascending=False).astype(int),
            "shap_after": after,
            "rank_after": after.rank(ascending=False).astype("Int64"),
            "corr_with_removed": X.corrwith(X[feature]),
            "corr_with_target": X.corrwith(y),
        }
    )
    comparison["rank_change"] = (comparison.rank_before - comparison.rank_after).astype(
        "Int64"
    )
    summary = {
        "feature": feature,
        "r2_before": float(r2_before),
        "r2_after": float(r2_after),
        "r2_cost": float(r2_before - r2_after),
        "sample": describe_sample(
            top_percent,
            bottom_percent,
            len(X),
            geography=config.describe_geography_in_eng("national_counties"),
        )[0]
        + (f", without {', '.join(exclude_groups)}" if exclude_groups else ""),
        "X": X,
        "y": y,
        "w": w,
        "geoids": unfiltered_df.loc[X.index, "GEOID"],
    }
    return comparison, summary


def run_substitution(
    feature: str | None = None,
    model_name: str = "rf",
    target: str = next(iter(REGRESSION_TARGETS)),
    seed: int = 1,
    folds: int = DEFAULT_FOLDS,
    top_percent: float | None = None,
    bottom_percent: float | None = None,
    exclude_groups: list[SlugGroupName] | None = None,
    counties: tuple[str, ...] = (),
) -> Path:
    """Run the test, print the verdict, write the table and any waterfalls."""
    comparison, summary = substitution_test(
        feature,
        model_name,
        target,
        seed,
        folds,
        top_percent,
        bottom_percent,
        exclude_groups,
    )
    removed = summary["feature"]

    print(f"\nremoved {removed} — {model_name}, weighted, {target}")
    print(f"sample: {summary['sample']}\n")

    cluster = comparison[
        (comparison.corr_with_removed.abs() >= CLUSTER_CORRELATION)
        & (comparison.index != removed)
    ]
    cluster = cluster.sort_values("rank_after")
    print(
        f"its correlated partners (|r| >= {CLUSTER_CORRELATION}), by rank AFTER removal:"
    )
    print(
        cluster.head(REPORTED_ROWS)[
            ["corr_with_removed", "corr_with_target", "rank_before", "rank_after"]
        ].to_string(float_format="%.3f")
    )

    others = comparison[comparison.index != removed]
    risen = others.nlargest(REPORTED_ROWS, "rank_change")
    print("\nfeatures that rose the most when it was removed:")
    print(
        risen[
            ["rank_before", "rank_after", "rank_change", "corr_with_removed"]
        ].to_string(float_format="%.3f")
    )

    print(
        f"\nout-of-fold R2: {summary['r2_before']:.3f} -> {summary['r2_after']:.3f} "
        f"(cost {summary['r2_cost']:+.3f}, {folds}-fold)"
    )
    verdict = (
        "redundant — the model did not need this column"
        if summary["r2_cost"] < 0.01
        else "load-bearing — removing it measurably hurts"
    )
    print(f"verdict: {verdict}")

    output_dir = (
        config.DATA_DIR
        / "prediction"
        / "regression"
        / f"substitution_{datetime.now(UTC).astimezone().date()}_{model_name}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"substitution_{removed}_{target}.csv"
    comparison.sort_values("rank_before").to_csv(output_path)

    for county in counties:
        plot_county_substitution(
            summary["X"],
            summary["y"],
            summary["w"],
            summary["geoids"],
            county,
            removed,
            model_name,
            target,
            seed,
            folds,
            summary["sample"],
            output_dir,
        )
    print(f"\noutput -> {output_dir}")
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m regression.substitution",
        description="Remove one feature, see what replaces it and what it costs.",
    )
    parser.add_argument(
        "--feature", default=None, help="default: the top feature by SHAP"
    )
    parser.add_argument("--model", choices=["rf", "lgbm"], default="rf")
    parser.add_argument(
        "--target",
        choices=list(REGRESSION_TARGETS),
        default=next(iter(REGRESSION_TARGETS)),
    )
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--folds", type=int, default=DEFAULT_FOLDS)
    parser.add_argument("--top-percent", type=float, default=None, metavar="X")
    parser.add_argument("--bottom-percent", type=float, default=None, metavar="X")
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=None,
        metavar="G",
        help="drop these feature groups first, to match an explain --exclude matrix",
    )
    parser.add_argument(
        "--counties",
        nargs="+",
        default=[],
        metavar="GEOID",
        help="also write before/after waterfalls for these counties",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_substitution(
        feature=args.feature,
        model_name=args.model,
        target=args.target,
        seed=args.seed,
        folds=args.folds,
        top_percent=args.top_percent,
        bottom_percent=args.bottom_percent,
        exclude_groups=args.exclude,
        counties=tuple(args.counties),
    )
