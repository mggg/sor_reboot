"""Driver for an individual-seed fit, explained with SHAP.

The group-stability driver (`regression.group_stability`) answers "how well do the
groups predict, across seeds"; this one fits ONE (model, target, seed) on
the runs' own sample and renders its explanation -- a beeswarm plus one
waterfall per requested county.

Every county is explained OUT OF FOLD -- by a model fit on the other folds,
never on that county -- so a waterfall shows the attributions behind a
prediction the model would make about a county it has not seen. The R² in
the beeswarm title is that same cross-validated fit. Accuracy claims still
belong to the scored runs.

Run: `python -m regression.explain [--model rf|lgbm] [--target T]
[--top-percent X | --bottom-percent X] [--counties GEOID ...] [--seed N]`.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

import numpy as np
import pandas as pd
import shap
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold

from build_dataset.feature_manifest import SlugGroupName, group_features
from build_dataset.ingest.geometry.geometry_api import load_county_geometry
from regression.shared.fit import fit_weighted, make_regressor
from regression.shared.prepare_df import describe_sample, prepare_df_for_regression
from regression.shared.run_config import REGRESSION_TARGETS
from regression.shared.shap_figures import county_label, plot_beeswarm, plot_waterfall
from utils import config

# The three largest Hispanic populations.
DEFAULT_COUNTIES = ("06037", "12086", "48201")


DEFAULT_FOLDS = 5


def run_single_seed_shap(
    model_name: str = "rf",
    target: str = next(iter(REGRESSION_TARGETS)),
    top_percent: float | None = None,
    bottom_percent: float | None = None,
    counties: tuple[str, ...] = DEFAULT_COUNTIES,
    seed: int = 1,
    exclude_groups: list[SlugGroupName] | None = None,
) -> None:
    """Fit one model on the runs' sample, write its SHAP figures.

    `exclude_groups` drops those feature groups' columns before fitting --
    the same ablation `group_stability --exclude` scores, explained
    rather than scored. Where the sweep says how much R2 a group was
    carrying, this says which features the model reaches for once it is
    gone.
    """
    unfiltered_df = pd.read_parquet(config.PROCESSED_NATIONAL_COUNTIES_PARQUET)
    # The scored runs' own sample logic: full-matrix complete-case + stratum.
    prepared_regression_data = prepare_df_for_regression(
        feature_groups=[],
        unfiltered_df=unfiltered_df,
        top_percent_hisp_pop=top_percent,
        bottom_percent_hisp_pop=bottom_percent,
    )
    feature_df = prepared_regression_data.full_feature_df
    target_values = prepared_regression_data.targets_df[target]
    weights = prepared_regression_data.hispanic_weights
    geoids = unfiltered_df.loc[feature_df.index, "GEOID"]

    ablation_suffix = ""
    if exclude_groups:
        dropped = {name for slug in exclude_groups for name in group_features([slug])}
        kept = [c for c in feature_df.columns if c not in dropped]
        # The stubs let a list key select a Series; a list of column names
        # always yields a DataFrame, so narrow it.
        ablated = feature_df[kept]
        print(
            f"ablation: {len(feature_df.columns)} -> {len(kept)} features "
            f"({len(dropped)} dropped with {', '.join(exclude_groups)})"
        )
        feature_df = ablated
        ablation_suffix = "_without-" + "-".join(exclude_groups)

    sample_note, stratum_suffix = describe_sample(
        top_percent, bottom_percent, n_rows=len(feature_df)
    )
    if exclude_groups:
        sample_note += f", without {', '.join(exclude_groups)}"
    output_dir = (
        config.DATA_DIR
        / "prediction"
        / "regression"
        / (
            f"shap_{datetime.now(UTC).astimezone().date()}_{model_name}"
            f"{stratum_suffix}{ablation_suffix}"
        )
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"{model_name}, weighted, {target}: fit on {sample_note}")

    explanation, predictions, out_of_fold_r2 = _fit_and_explain(
        model_name, target, seed, feature_df, target_values, weights
    )

    model_note = f"{model_name} (seed {seed}), weighted"
    plot_beeswarm(
        explanation,
        title=(
            f"SHAP beeswarm: {model_note} - {target}\n"
            f"{sample_note} — out-of-fold R² {out_of_fold_r2:.2f} ({DEFAULT_FOLDS}-fold, seed {seed})"
        ),
        output_path=output_dir / "shap_beeswarm.png",
    )

    county_names = load_county_geometry().set_index("GEOID")["NAME"]
    for geoid in counties:
        matches = geoids[geoids == geoid]
        if matches.empty:
            print(f"  {geoid}: not in this sample, skipped")
            continue
        # numpy, not Index.get_loc: its return type is a union of int,
        # slice and mask. geoids shares feature_df's index, so positions match.
        row_position = int(np.flatnonzero(geoids.to_numpy() == geoid)[0])
        plot_waterfall(
            explanation[row_position],
            county_title=county_label(geoid, county_names),
            actual=target_values.iloc[row_position],
            predicted=predictions.iloc[row_position],
            target_label=REGRESSION_TARGETS[target],
            model_note=model_note,
            sample_note=sample_note,
            output_path=output_dir / f"shap_waterfall_{geoid}.png",
        )
    print(f"outputs -> {output_dir}")


def _fit_and_explain(
    model_name: str,
    target: str,
    seed: int,
    feature_df: pd.DataFrame,
    target_values: pd.Series,
    weights: pd.Series,
    folds: int = DEFAULT_FOLDS,
):
    """(SHAP explanation, predictions, out-of-fold R²), every row held out.

    Each county is explained by the fold model that did NOT train on it.
    Explaining an in-sample fit was the earlier behaviour and it flattered
    the result: a forest largely reproduces its training rows, so the
    waterfall showed a prediction equal to the county's own value and the
    attributions explained that memorised number rather than one the model
    would make about a county it had never seen.

    Each fold model carries its own baseline, so the `E[f(X)]` a waterfall
    prints is that fold's mean prediction -- they differ slightly across
    counties, which is honest rather than tidy.

    Parameters
    ----------
    model_name : str
        A `make_regressor` key; the tree models only (SHAP TreeExplainer).
    target : str
        The target column name, for the scored metrics.
    seed : int
        Seeds the fold shuffle and the estimators.
    feature_df, target_values, weights : pandas.DataFrame, pandas.Series, pandas.Series
        The prepared sample, aligned.
    folds : int
        Number of cross-validation folds.

    Returns
    -------
    tuple
        (shap.Explanation over every row, out-of-fold predictions,
        weighted out-of-fold R²).
    """
    n_rows, n_features = feature_df.shape
    shap_values = np.zeros((n_rows, n_features))
    base_values = np.zeros(n_rows)
    predictions = np.zeros(n_rows)

    splitter = KFold(n_splits=folds, shuffle=True, random_state=seed)
    for fold, (train_rows, test_rows) in enumerate(splitter.split(feature_df), start=1):
        model = make_regressor(model_name, seed)
        fit_weighted(
            model,
            feature_df.iloc[train_rows],
            target_values.iloc[train_rows],
            weights.iloc[train_rows].to_numpy(),
        )
        held_out = feature_df.iloc[test_rows]
        explanation = shap.TreeExplainer(model)(held_out)
        # asarray: shap's stubs do not type Explanation.values as an array,
        # so .ndim is unknown to the checker; at runtime it is an ndarray.
        if np.asarray(explanation.values).ndim == 3:  # some add an output axis
            explanation = explanation[..., 0]
        shap_values[test_rows] = explanation.values
        base_values[test_rows] = explanation.base_values
        predictions[test_rows] = np.asarray(model.predict(held_out))
        print(
            f"  fold {fold}/{folds}: {len(train_rows)} fit, {len(test_rows)} explained"
        )

    out_of_fold_r2 = float(r2_score(target_values, predictions, sample_weight=weights))
    stitched = shap.Explanation(
        values=shap_values,
        base_values=base_values,
        data=feature_df.to_numpy(),
        feature_names=list(feature_df.columns),
    )
    return stitched, pd.Series(predictions, index=feature_df.index), out_of_fold_r2


def _parse_args():
    parser = argparse.ArgumentParser(
        prog="python -m regression.explain",
        description="One explained fit: SHAP beeswarm + county waterfalls.",
    )
    parser.add_argument("--model", choices=["rf", "lgbm"], default="rf")
    parser.add_argument(
        "--target",
        default=next(iter(REGRESSION_TARGETS)),
        choices=list(REGRESSION_TARGETS),
    )
    parser.add_argument("--top-percent", type=float, default=None, metavar="X")
    parser.add_argument("--bottom-percent", type=float, default=None, metavar="X")
    parser.add_argument(
        "--counties",
        nargs="+",
        default=list(DEFAULT_COUNTIES),
        metavar="GEOID",
        help="counties to draw waterfalls for (5-digit GEOIDs)",
    )
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=None,
        metavar="G",
        help="drop these feature groups before fitting, to explain the same "
        "ablation `group_stability --exclude` scores",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_single_seed_shap(
        model_name=args.model,
        target=args.target,
        top_percent=args.top_percent,
        bottom_percent=args.bottom_percent,
        counties=tuple(args.counties),
        seed=args.seed,
        exclude_groups=args.exclude,
    )
