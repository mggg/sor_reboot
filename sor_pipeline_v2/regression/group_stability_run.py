"""One R² per (group x model x weighting x target) cell, repeated across seeds:
how much does each feature group explain of Hispanic race choice on its own,
against the full-matrix baseline?

Run `python -m regression.group_stability_run -h`. Outputs (per-fit and
summary CSVs, comparison figures) land in a run directory named by the
date, seeds, and any non-default options.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from itertools import product

import pandas as pd
from tqdm import tqdm

from build_dataset.ingest.store_df import load_df_from_parquet
from regression.fit import MODEL_LABELS, split_fit_and_score_regression
from regression.prepare_df import prepare_df_for_regression
from regression.run_config import (
    FULL,
    REGRESSION_TARGETS,
    FullRegressionModelRunParams,
    RegressionParameters,
    create_run_dir,
)
from regression.viz import group_model_comparisons
from utils import config


def run_group_stability(
    full_regression_run_params: FullRegressionModelRunParams,
) -> pd.DataFrame:
    output_dir = create_run_dir(run_params=full_regression_run_params)
    unfiltered_df = load_df_from_parquet(config.PROCESSED_NATIONAL_COUNTIES_PARQUET)

    prepared_regression_data = prepare_df_for_regression(
        feature_groups=full_regression_run_params.feature_groups,
        unfiltered_df=unfiltered_df,
        top_percent_hisp_pop=full_regression_run_params.top_percent,
        bottom_percent_hisp_pop=full_regression_run_params.bottom_percent,
    )
    full_feature_df = prepared_regression_data.full_feature_df
    n_counties = len(full_feature_df)
    targets = list(REGRESSION_TARGETS.keys())
    seeds = full_regression_run_params.rng_seeds
    tree_params = full_regression_run_params.regression_tree_params

    weightings = {
        "unweighted": None,
        "weighted": prepared_regression_data.hispanic_weights,
    }

    matrices: dict[str, pd.DataFrame] = {}
    if full_regression_run_params.include_full_baseline:
        matrices[FULL] = full_feature_df
    matrices.update(
        {
            slug: full_feature_df[names]
            for slug, names in prepared_regression_data.feature_names_by_group.items()
        }
    )

    n_fits = (
        len(seeds) * len(matrices) * len(MODEL_LABELS) * len(weightings) * len(targets)
    )
    print(
        f"group stability -> {output_dir}\n"
        f"{n_counties:,} counties (complete on the full matrix) · "
        f"matrices: {', '.join(matrices)} · "
        f"params {tree_params} · {len(seeds)} seeds -> {n_fits} fits"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    with tqdm(total=n_fits, desc="group stability", unit="fit") as progress:
        for seed in seeds:
            for (group_name, group_df), model, weight, target in product(
                matrices.items(), MODEL_LABELS, weightings.values(), targets
            ):
                metrics = split_fit_and_score_regression(
                    group_df,
                    prepared_regression_data.targets_df[target],
                    model,
                    seed,
                    weights=weight,
                    params=tree_params,
                )
                rows.append(
                    {
                        "group": group_name,
                        "target": target,
                        "n_features": group_df.shape[1],
                        **asdict(metrics),
                    }
                )
                progress.update(1)
            progress.set_postfix(seed=seed)

    by_seed = pd.DataFrame(rows)
    summary = _summarize_across_seeds(by_seed)

    by_seed.to_csv(output_dir / "group_metrics_by_seed.csv", index=False)
    summary.to_csv(output_dir / "group_summary.csv", index=False)

    if full_regression_run_params.top_percent is not None:
        sample_note = (
            f"top {full_regression_run_params.top_percent:g}% of counties "
            f"by Hispanic population (n={n_counties:,})"
        )
    elif full_regression_run_params.bottom_percent is not None:
        sample_note = (
            f"bottom {full_regression_run_params.bottom_percent:g}% of counties "
            f"by Hispanic population (n={n_counties:,})"
        )
    else:
        sample_note = f"all complete-case counties (n={n_counties:,})"
    group_model_comparisons.plot_group_comparison(
        summary, output_dir, n_seeds=len(seeds), sample_note=sample_note
    )
    print(f"wrote group-stability outputs -> {output_dir}")
    return summary


# One summary row per cell of the experiment grid (the four dimensions the
# run loop iterates), aggregating across seeds. output column -> (input
# column, statistic); r2 gets its full spread because the seed-noise reading
# rule needs sd, min and max, ess gets min because the weighted reading rule
# needs the worst fold.
GRID_KEYS = ["group", "model", "weighting", "target"]
SEED_AGGREGATIONS = {
    "n_features": ("n_features", "first"),
    "mean_r2": ("r2", "mean"),
    "sd_r2": ("r2", "std"),
    "min_r2": ("r2", "min"),
    "max_r2": ("r2", "max"),
    "mean_rmse": ("rmse", "mean"),
    "mean_ess": ("ess", "mean"),
    "min_ess": ("ess", "min"),
    "max_ess": ("ess", "max"),
}


def _summarize_across_seeds(by_seed: pd.DataFrame) -> pd.DataFrame:
    """Collapse per-fit rows to mean ± spread per experiment-grid cell."""
    return by_seed.groupby(GRID_KEYS).agg(**SEED_AGGREGATIONS).reset_index()


def _parse_args() -> FullRegressionModelRunParams:
    """CLI -> a validated params object ('full' split off here; a missing
    --groups normalizes to every group in the params' __post_init__)."""
    defaults = RegressionParameters()
    parser = argparse.ArgumentParser(
        description="Group-stability regression sweep (three peer models)."
    )
    parser.add_argument(
        "--seeds",
        nargs=2,
        type=int,
        default=[1, 50],
        metavar=("LO", "HI"),
        help="inclusive seed range (default: 1 50)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=defaults.max_depth,
        help="tree depth cap for rf and lgbm",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=defaults.n_estimators,
        help="number of trees for rf and lgbm",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=defaults.learning_rate,
        help="lgbm learning rate",
    )
    parser.add_argument(
        "--num-leaves",
        type=int,
        default=defaults.num_leaves,
        help="lgbm leaf cap",
    )
    parser.add_argument(
        "--top-percent",
        type=float,
        default=None,
        metavar="X",
        help="restrict to the counties in the top X%% by Hispanic population "
        "(cutoff computed after complete-case filtering)",
    )
    parser.add_argument(
        "--bottom-percent",
        type=float,
        default=None,
        metavar="X",
        help="restrict to the counties in the bottom X%% by Hispanic "
        "population; --bottom-percent 90 is the exact complement of "
        "--top-percent 10 (same cutoff, opposite side)",
    )
    parser.add_argument(
        "--groups",
        nargs="+",
        default=None,
        metavar="G",
        help="run only these matrices: group slugs (mobility geography) "
        "and/or 'full' for the baseline; default runs full + all groups. "
        "Rows stay complete-case on the FULL matrix either way, so "
        "subset runs remain comparable to full runs.",
    )
    args = parser.parse_args()

    # 'full' is the default request
    if args.groups is None:
        feature_groups = None
        include_full_baseline = True
    else:
        feature_groups = [g for g in args.groups if g != FULL]
        include_full_baseline = FULL in args.groups
    lo, hi = args.seeds
    return FullRegressionModelRunParams(
        rng_seeds=list(range(lo, hi + 1)),
        regression_tree_params=RegressionParameters(
            max_depth=args.max_depth,
            n_estimators=args.n_estimators,
            learning_rate=args.learning_rate,
            num_leaves=args.num_leaves,
        ),
        feature_groups=feature_groups,
        top_percent=args.top_percent,
        bottom_percent=args.bottom_percent,
        include_full_baseline=include_full_baseline,
    )


if __name__ == "__main__":
    run_group_stability(_parse_args())
