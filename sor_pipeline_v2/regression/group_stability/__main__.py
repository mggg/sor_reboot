"""One R² per (group x model x weighting x target) cell, repeated across seeds:
how much does each feature group explain of Hispanic race choice on its own,
against the full-matrix baseline?

Run `python -m regression.group_stability -h`. Outputs (per-fit and
summary CSVs, comparison figures) land in a run directory named by the
date, seeds, and any non-default options.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from itertools import product
from typing import get_args

import pandas as pd
from tqdm import tqdm

from build_dataset.feature_manifest import MODEL_GROUPS, group_features
from build_dataset.ingest.fetch_and_store.store_df import load_df_from_parquet
from regression.group_stability import figures
from regression.shared.fit import MODEL_LABELS, split_fit_and_score_regression
from regression.shared.prepare_df import prepare_df_for_regression
from regression.shared.run_config import (
    FULL,
    FULL_MINUS,
    REGRESSION_TARGETS,
    FullRegressionModelRunParams,
    RegressionParameters,
    absent_variables,
    create_run_dir,
)
from utils import config

# One summary row per cell of the experiment grid (the four dimensions the
# run loop iterates), aggregating across seeds. output column -> (input
# column, statistic); r2 gets its full spread because the seed-noise reading
# rule needs sd, min and max, ess gets min because the weighted reading rule
# needs the worst fold.
GRID_KEYS = ["group", "model", "weighting", "target"]
SEED_AGGREGATIONS = {
    # Both constant across a run -- every fit scores the same rows on
    # the same 80/20 split -- but carried into the summary so that file
    # says on its own how large the sample was, as it already does for
    # the feature count. n_test is here because it is the DENOMINATOR of
    # the ess columns below: ess is the effective size of the held-out
    # fold, which is what an R2 is scored on, and it reads as
    # implausibly small next to n unless n_test is beside it.
    "n": ("n", "first"),
    "n_test": ("n_test", "first"),
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


def run_group_stability(
    full_regression_run_params: FullRegressionModelRunParams,
) -> pd.DataFrame:
    output_dir = create_run_dir(run_params=full_regression_run_params)
    level = full_regression_run_params.level
    input_path = config.processed_parquet_path(
        level, full_regression_run_params.state_fips
    )
    unfiltered_df = load_df_from_parquet(input_path)
    # Tracts lack five declared predictors, so the "full matrix" is the
    # full matrix FOR THIS LEVEL; see feature_manifest.TRACT_ABSENT_VARIABLES.
    exclude_variables = absent_variables(level)

    prepared_regression_data = prepare_df_for_regression(
        feature_groups=full_regression_run_params.feature_groups,
        unfiltered_df=unfiltered_df,
        top_percent_hisp_pop=full_regression_run_params.top_percent,
        bottom_percent_hisp_pop=full_regression_run_params.bottom_percent,
        exclude_variables=exclude_variables,
    )
    full_feature_df = prepared_regression_data.full_feature_df
    n_rows = len(full_feature_df)
    # Named, not just "tracts": a figure read on its own has to say
    # WHICH tracts, and a CA-only run looks identical to a national one
    # otherwise.
    geography = config.describe_geography(level, full_regression_run_params.state_fips)
    targets = list(REGRESSION_TARGETS.keys())
    seeds = full_regression_run_params.rng_seeds
    tree_params = full_regression_run_params.regression_tree_params

    weightings = {
        "unweighted": None,
        "weighted": prepared_regression_data.hispanic_weights,
    }

    run_group_name_to_features_df: dict[str, pd.DataFrame] = {}
    if full_regression_run_params.include_full_baseline:
        run_group_name_to_features_df[FULL] = full_feature_df
    run_group_name_to_features_df.update(
        {
            group_name: full_feature_df[feature_names]
            for group_name, feature_names in prepared_regression_data.feature_names_by_group.items()
        }
    )
    # The ablation: the full matrix minus the excluded groups' columns, fit
    # alongside the untouched full baseline so the pair is directly
    # comparable -- same rows, same seeds, same split.
    if full_regression_run_params.exclude_groups:
        dropped = {
            name
            for slug in full_regression_run_params.exclude_groups
            for name in group_features([slug], exclude_variables)
        }
        kept = [c for c in full_feature_df.columns if c not in dropped]
        ablation_name = FULL_MINUS + "-".join(full_regression_run_params.exclude_groups)
        # The stubs let a list key select a Series; a list of column names
        # always yields a DataFrame, so narrow it.
        ablation_matrix = full_feature_df[kept]
        run_group_name_to_features_df[ablation_name] = ablation_matrix
        print(
            f"ablation {ablation_name}: {len(full_feature_df.columns)} -> {len(kept)} "
            f"features ({len(dropped)} dropped)"
        )

    n_fits = (
        len(seeds)
        * len(run_group_name_to_features_df)
        * len(MODEL_LABELS)
        * len(weightings)
        * len(targets)
    )
    print(
        f"group stability -> {output_dir}\n"
        f"{input_path.name} · "
        f"{n_rows:,} {geography} (complete on the full matrix) · "
        f"{len(full_feature_df.columns)} features · "
        f"matrices: {', '.join(run_group_name_to_features_df)} · "
        f"params {tree_params} · {len(seeds)} seeds -> {n_fits} fits"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    # One CSV per finished seed, so a run killed partway keeps every seed
    # it completed instead of nothing.
    seed_dir = output_dir / "by_seed"
    seed_dir.mkdir(exist_ok=True)

    run_results = []
    with tqdm(total=n_fits, desc="group stability", unit="fit") as progress:
        for seed in seeds:  # Make one for loop; also merge with tqdm
            seed_results = []
            for (group_name, group_df), model, weight, target in product(
                run_group_name_to_features_df.items(),
                MODEL_LABELS,
                weightings.values(),
                targets,
            ):
                seed_results.append(
                    asdict(
                        split_fit_and_score_regression(
                            group_name,
                            target,
                            group_df,
                            prepared_regression_data.targets_df[target],
                            model,
                            seed,
                            weights=weight,
                            params=tree_params,
                        )
                    )
                )
                progress.update(1)
            pd.DataFrame(seed_results).to_csv(
                seed_dir / f"seed_{seed}.csv", index=False
            )
            run_results.extend(seed_results)
            progress.set_postfix(seed=seed)

    by_seed = pd.DataFrame(run_results)
    summary = _summarize_across_seeds(by_seed)

    by_seed.to_csv(output_dir / "group_metrics_by_seed.csv", index=False)
    summary.to_csv(output_dir / "group_summary.csv", index=False)

    if full_regression_run_params.top_percent is not None:
        sample_note = (
            f"top {full_regression_run_params.top_percent:g}% of {geography} "
            f"by Hispanic population (n={n_rows:,})"
        )
    elif full_regression_run_params.bottom_percent is not None:
        sample_note = (
            f"bottom {full_regression_run_params.bottom_percent:g}% of {geography} "
            f"by Hispanic population (n={n_rows:,})"
        )
    else:
        sample_note = f"all complete-case {geography} (n={n_rows:,})"
    figures.plot_group_comparison(
        summary, output_dir, n_seeds=len(seeds), sample_note=sample_note
    )
    print(f"wrote group-stability outputs -> {output_dir}")
    return summary


def _summarize_across_seeds(by_seed: pd.DataFrame) -> pd.DataFrame:
    """Collapse per-fit rows to mean ± spread per experiment-grid cell."""
    return by_seed.groupby(GRID_KEYS).agg(**SEED_AGGREGATIONS).reset_index()


def _parse_args() -> FullRegressionModelRunParams:
    """CLI -> a validated params object ('full' split off here; a missing
    --groups normalizes to every group in the params' __post_init__)."""
    defaults = RegressionParameters()
    parser = argparse.ArgumentParser(
        prog="python -m regression.group_stability",
        description="Group-stability regression sweep (three peer models).",
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
        type=int,
        default=None,
        metavar="X",
        help="restrict to the rows in the top X%% by Hispanic population "
        "(cutoff computed after complete-case filtering)",
    )
    parser.add_argument(
        "--bottom-percent",
        type=int,
        default=None,
        metavar="X",
        help="restrict to the rows in the bottom X%% by Hispanic "
        "population; --bottom-percent 90 is the exact complement of "
        "--top-percent 10 (same cutoff, opposite side)",
    )
    parser.add_argument(
        "--level",
        choices=list(get_args(config.GeographicBuildLevel)),
        default="national_counties",
        help="which dataset to fit (default: national_counties)",
    )
    parser.add_argument(
        "--states",
        nargs="+",
        default=None,
        metavar="FIPS",
        help="tracts only: the state scope the build covered, e.g. --states 06 "
        "reads processed_states-06.parquet; omit for the national tract file",
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
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=None,
        metavar="G",
        help="also fit the full matrix WITHOUT these groups (an ablation), "
        "alongside the untouched full baseline: --exclude geography answers "
        "'what survives when the model cannot use location?'",
    )
    args = parser.parse_args()

    # 'full' is the default request
    if args.groups is None:
        feature_groups = list(MODEL_GROUPS)
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
        exclude_groups=args.exclude or [],
        level=args.level,
        state_fips=args.states,
    )


if __name__ == "__main__":
    run_group_stability(_parse_args())
