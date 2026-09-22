from dataclasses import dataclass

import pandas as pd

from build_dataset.feature_manifest import (
    SlugGroupName,
    all_model_features,
    group_features,
)
from model_utils.matrix import feature_frame
from regression.run_config import REGRESSION_TARGETS, WEIGHT_COL


@dataclass(frozen=True)
class PreparedRegressionData:
    """The aligned inputs for one run: same counties, same order, everywhere.

    All four pieces are built from ONE row selection, so features, targets
    and weights cannot be paired across different filters.
    """

    full_feature_df: pd.DataFrame
    targets_df: pd.DataFrame
    hispanic_weights: pd.Series
    feature_names_by_group: dict[SlugGroupName, list[str]]


def prepare_df_for_regression(
    feature_groups: list[SlugGroupName],
    unfiltered_df: pd.DataFrame,
    top_percent_hisp_pop: int | None = None,
    bottom_percent_hisp_pop: int | None = None,
) -> PreparedRegressionData:
    """The regression sample, aligned: full feature matrix, targets and
    weights on the same kept rows, plus the group -> feature-names map for
    slicing per-group matrices.

    `feature_groups` holds real group slugs only: "full" is a runner
    concept, resolved before this function is called. The full-matrix
    baseline needs no entry here: it is the returned frame itself, unsliced.

    The kept rows are ALWAYS the counties complete on the FULL matrix and
    targets, whichever groups are being fit: subset runs must score on the
    same counties as full runs, or their R² values are not comparable.
    """
    feature_names_by_group = _feature_slugs_to_var_names(feature_groups)

    full_feature_df = feature_frame(unfiltered_df, all_model_features())
    features_and_targets = pd.concat(
        [full_feature_df, unfiltered_df[list(REGRESSION_TARGETS)]], axis=1
    )
    complete_features = features_and_targets.notna().all(axis=1)
    if not complete_features.all():
        # The blame ledger: which columns cost which counties -- ex. 3,221 -> 2,913
        n_kept = int(complete_features.sum())
        print(
            f"complete cases: {n_kept:,} of {len(features_and_targets):,} "
            f"counties ({len(features_and_targets) - n_kept:,} dropped)"
        )
        missing_counts = features_and_targets.loc[~complete_features].isna().sum()
        for column, count in missing_counts.sort_values(ascending=False).items():
            if count > 0:
                print(f"  missing {column}: {int(count):,} counties")
    if top_percent_hisp_pop is not None or bottom_percent_hisp_pop is not None:
        counties_to_keep = _filter_top_or_bottom(
            df=unfiltered_df,
            full_features_to_keep=complete_features,
            top_percent_hisp_pop=top_percent_hisp_pop,
            bottom_percent_hisp_pop=bottom_percent_hisp_pop,
        )
    else:
        counties_to_keep = complete_features

    kept_counties = full_feature_df.index[counties_to_keep]
    return PreparedRegressionData(
        full_feature_df=full_feature_df.loc[kept_counties],
        targets_df=unfiltered_df.loc[kept_counties, list(REGRESSION_TARGETS)],
        hispanic_weights=unfiltered_df.loc[kept_counties, WEIGHT_COL],
        feature_names_by_group=feature_names_by_group,
    )


def _feature_slugs_to_var_names(
    feature_groups_slugs: list[SlugGroupName],
) -> dict[SlugGroupName, list[str]]:
    """Group slug -> that group's predictor column names, in manifest order."""
    return {slug: group_features([slug]) for slug in feature_groups_slugs}


def _filter_top_or_bottom(
    df: pd.DataFrame,
    full_features_to_keep: pd.Series,
    top_percent_hisp_pop: int | None = None,
    bottom_percent_hisp_pop: int | None = None,
) -> pd.Series:
    """Shrink the kept rows to one stratum by Hispanic population.

    `top_percent_hisp_pop=10` keeps counties AT OR ABOVE the 90th percentile;
    `bottom_percent_hisp_pop=90` keeps counties BELOW it -- the same cutoff,
    so the two runs partition the kept counties exactly.
    """
    hispanic_counts = df.loc[full_features_to_keep, WEIGHT_COL]
    if top_percent_hisp_pop is not None:
        cutoff = hispanic_counts.quantile(1 - top_percent_hisp_pop / 100)
        counties_to_keep = (df[WEIGHT_COL] >= cutoff) & full_features_to_keep
    else:
        cutoff = hispanic_counts.quantile(bottom_percent_hisp_pop / 100)
        counties_to_keep = (df[WEIGHT_COL] < cutoff) & full_features_to_keep
    return counties_to_keep
