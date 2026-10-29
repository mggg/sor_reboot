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

from build_dataset.ingest.fetch_and_store.store_df import load_df_from_parquet
from build_dataset.model_groups import MODEL_GROUPS, group_features
from model_utils.split import SplitGrouping, county_groups
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
    run_file,
)
from regression.shared.run_metadata import (
    describe_features,
    describe_sample,
    finish_run_metadata,
    git_state,
    start_run_metadata,
    warn_if_uncommitted,
)
from utils import config

# Collapse each combination's per-seed rows into one summary row.
# Stats are: output column -> (input column, statistic).
SUMMARY_ROW_KEYS = ["group", "model", "weighting", "target"]
ACROSS_SEED_STATS = {
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
    git = git_state()
    warn_if_uncommitted(git)
    output_dir = create_run_dir(run_params=full_regression_run_params)
    geo_level = full_regression_run_params.geo_level
    input_path = config.processed_parquet_path(
        geo_level, full_regression_run_params.state_fips
    )
    unfiltered_df = load_df_from_parquet(input_path)
    # Tracts don't have all the predictors that counties do due to the
    # absence of certain variables at the tract level.
    exclude_variables = absent_variables(geo_level)

    prepared_regression_data = prepare_df_for_regression(
        feature_groups=full_regression_run_params.feature_groups,
        unfiltered_df=unfiltered_df,
        top_percent_hisp_pop=full_regression_run_params.top_percent,
        bottom_percent_hisp_pop=full_regression_run_params.bottom_percent,
        exclude_variables=exclude_variables,
    )
    full_feature_df = prepared_regression_data.full_feature_df
    n_rows = len(full_feature_df)

    geography_in_eng = config.describe_geography_in_eng(
        geo_level, full_regression_run_params.state_fips
    )
    targets = list(REGRESSION_TARGETS.keys())
    seeds = full_regression_run_params.rng_seeds
    tree_params = full_regression_run_params.regression_tree_params

    # If split grouping is county, then tracts get held out based on their county
    # membership (not purely random at the tract level). This is meant to help avoid
    # the model simply memorizing similar-looking tract features rather than learning
    # generalizable patterns.
    split_groups = (
        county_groups(unfiltered_df.loc[full_feature_df.index, "GEOID"])
        if full_regression_run_params.split_grouping == "county"
        else None
    )

    hisp_weightings = {
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

    if full_regression_run_params.exclude_groups:
        dropped_groups = {
            name
            for feat_group in full_regression_run_params.exclude_groups
            for name in group_features([feat_group], exclude_variables)
        }
        kept = [c for c in full_feature_df.columns if c not in dropped_groups]
        ablation_name = FULL_MINUS + "-".join(full_regression_run_params.exclude_groups)

        ablation_matrix = full_feature_df[kept]
        run_group_name_to_features_df[ablation_name] = ablation_matrix
        print(
            f"ablation {ablation_name}: {len(full_feature_df.columns)} -> {len(kept)} "
            f"features ({len(dropped_groups)} dropped)"
        )

    n_fits = (
        len(seeds)
        * len(run_group_name_to_features_df)
        * len(MODEL_LABELS)
        * len(hisp_weightings)
        * len(targets)
    )
    print(
        f"group stability -> {output_dir}\n"
        f"{input_path.name} · "
        f"{n_rows:,} {geography_in_eng} (complete on the full matrix) · "
        f"{len(full_feature_df.columns)} features · "
        f"matrices: {', '.join(run_group_name_to_features_df)} · "
        f"params {tree_params} · split grouping: {full_regression_run_params.split_grouping} · "
        f"{len(seeds)} seeds -> {n_fits} fits"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = start_run_metadata(
        output_dir,
        git,
        settings=asdict(full_regression_run_params),
        inputs=[input_path],
        sample=describe_sample(
            unfiltered_df,
            full_feature_df.index,
            [*full_feature_df.columns, *targets],
        ),
        features=describe_features(list(full_feature_df.columns)),
    )

    seed_dir = output_dir / "by_seed"
    seed_dir.mkdir(exist_ok=True)

    run_results = []
    with tqdm(total=n_fits, desc="group stability", unit="fit") as progress:
        for seed in seeds:
            seed_results = []
            for (group_name, group_df), model, weight, target in product(
                run_group_name_to_features_df.items(),
                MODEL_LABELS,
                hisp_weightings.values(),
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
                            groups=split_groups,
                        )
                    )
                )
                progress.update(1)
            pd.DataFrame(seed_results).to_csv(
                run_file(output_dir, f"seed_{seed}", subdir=seed_dir.name),
                index=False,
            )
            run_results.extend(seed_results)
            progress.set_postfix(seed=seed)

    by_seed = pd.DataFrame(run_results)
    summary = _summarize_across_seeds(by_seed)

    by_seed.to_csv(run_file(output_dir, "group_metrics_by_seed"), index=False)
    summary.to_csv(run_file(output_dir, "group_summary"), index=False)

    if full_regression_run_params.top_percent is not None:
        sample_note = (
            f"top {full_regression_run_params.top_percent:g}% of {geography_in_eng} "
            f"by Hispanic population (n={n_rows:,})"
        )
    elif full_regression_run_params.bottom_percent is not None:
        sample_note = (
            f"bottom {full_regression_run_params.bottom_percent:g}% of {geography_in_eng} "
            f"by Hispanic population (n={n_rows:,})"
        )
    else:
        sample_note = f"all complete-case {geography_in_eng} (n={n_rows:,})"
    figures.plot_group_comparison(
        summary, output_dir, n_seeds=len(seeds), sample_note=sample_note
    )
    finish_run_metadata(output_dir, metadata)
    print(f"wrote group-stability outputs -> {output_dir}")
    return summary


def _summarize_across_seeds(by_seed: pd.DataFrame) -> pd.DataFrame:
    """Collapse per-fit rows to mean ± spread per experiment-grid cell."""
    return by_seed.groupby(SUMMARY_ROW_KEYS).agg(**ACROSS_SEED_STATS).reset_index()


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
    parser.add_argument(
        "--split-grouping",
        choices=list(get_args(SplitGrouping)),
        default="none",
        help="which tracts the 80/20 train/test split keeps together. "
        "'none' (default): each tract goes to train or test independently. "
        "'county' (tract data only): a county's tracts all go to the same "
        "side, so the model is trained and scored on different counties",
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
        geo_level=args.level,
        state_fips=args.states,
        split_grouping=args.split_grouping,
    )


if __name__ == "__main__":
    run_group_stability(_parse_args())
