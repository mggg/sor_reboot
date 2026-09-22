"""Driver for an individual-seed fit, explained with SHAP.

The group-stability driver (`regression.group_stability_run`) answers "how well do the
groups predict, across seeds"; this one fits ONE (model, target, seed) on
the runs' own sample and renders its explanation -- a beeswarm plus one
waterfall per requested county.

The explained model is fit on ALL kept rows (explanation wants the model to
have seen the counties being explained); the held-out R² in the beeswarm
title comes from the pipeline's own evaluator at the same seed. Accuracy
claims belong to the scored runs.

Run: `python -m regression.shap_run [--model rf|lgbm] [--target T]
[--top-percent X | --bottom-percent X] [--counties GEOID ...] [--seed N]`.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

import pandas as pd
import shap

from build_dataset.ingest.geometry.geometry_api import load_county_geometry
from regression.fit import make_regressor, split_fit_and_score_regression
from regression.prepare_df import prepare_df_for_regression
from regression.run_config import REGRESSION_TARGETS
from regression.viz.shap_figures import county_label, plot_beeswarm, plot_waterfall
from utils import config

# The three largest Hispanic populations.
DEFAULT_COUNTIES = ("06037", "12086", "48201")


def run_single_seed_shap(
    model_name: str = "rf",
    target: str = next(iter(REGRESSION_TARGETS)),
    top_percent: float | None = None,
    bottom_percent: float | None = None,
    counties: tuple[str, ...] = DEFAULT_COUNTIES,
    seed: int = 1,
) -> None:
    """Fit one model on the runs' sample, write its SHAP figures."""
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

    sample_note, stratum_suffix = _describe_sample(
        top_percent, bottom_percent, n_counties=len(feature_df)
    )
    output_dir = (
        config.DATA_DIR
        / "prediction"
        / "regression"
        / f"shap_{datetime.now(UTC).astimezone().date()}_{model_name}{stratum_suffix}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"{model_name}, weighted, {target}: fit on {sample_note}")

    explanation, predictions, held_out_r2 = _fit_and_explain(
        model_name, seed, feature_df, target_values, weights
    )

    model_note = f"{model_name} (seed {seed}), weighted"
    plot_beeswarm(
        explanation,
        title=(
            f"SHAP beeswarm: {model_note} - {target}\n"
            f"{sample_note} — held-out R² {held_out_r2:.2f} (one split, seed {seed})"
        ),
        output_path=output_dir / "shap_beeswarm.png",
    )

    county_names = load_county_geometry().set_index("GEOID")["NAME"]
    for geoid in counties:
        matches = geoids[geoids == geoid]
        if matches.empty:
            print(f"  {geoid}: not in this sample, skipped")
            continue
        row_position = feature_df.index.get_loc(matches.index[0])
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
    seed: int,
    feature_df: pd.DataFrame,
    target_values: pd.Series,
    weights: pd.Series,
):
    """(SHAP explanation, predictions, held-out R²) for one weighted fit."""
    held_out_r2 = split_fit_and_score_regression(
        feature_df, target_values, model_name, seed, weights=weights
    ).r2
    model = make_regressor(model_name, seed)
    model.fit(feature_df, target_values, sample_weight=weights)
    explanation = shap.TreeExplainer(model)(feature_df)
    if explanation.values.ndim == 3:  # some explainers add an output axis
        explanation = explanation[..., 0]
    predictions = pd.Series(model.predict(feature_df), index=feature_df.index)
    return explanation, predictions, held_out_r2


def _describe_sample(
    top_percent: float | None, bottom_percent: float | None, n_counties: int
) -> tuple[str, str]:
    """(title text, output-dir suffix) for the sample the model saw."""
    if top_percent is not None:
        stratum = f"top {top_percent:g}% by Hispanic population"
        suffix = f"_top-{top_percent:g}pct"
    elif bottom_percent is not None:
        stratum = f"bottom {bottom_percent:g}% by Hispanic population"
        suffix = f"_bottom-{bottom_percent:g}pct"
    else:
        stratum, suffix = "all complete-case counties", ""
    return f"{stratum} (n={n_counties:,})", suffix


def _parse_args():
    parser = argparse.ArgumentParser(
        description="One explained fit: SHAP beeswarm + county waterfalls."
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
    )
