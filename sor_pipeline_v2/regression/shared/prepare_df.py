from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from build_dataset.model_groups import (
    ModelGroupName,
    all_model_features,
    group_features,
)
from model_utils.matrix import feature_frame
from regression.shared.run_config import REGRESSION_TARGETS, WEIGHT_COL


@dataclass(frozen=True)
class PreparedRegressionData:
    """The aligned inputs for one run: same rows, same order, everywhere.

    All four pieces are built from ONE row selection, so features, targets
    and weights cannot be paired across different filters.
    """

    full_feature_df: pd.DataFrame
    targets_df: pd.DataFrame
    hispanic_weights: pd.Series
    feature_names_by_group: dict[ModelGroupName, list[str]]


def prepare_df_for_regression(
    feature_groups: list[ModelGroupName],
    unfiltered_df: pd.DataFrame,
    top_percent_hisp_pop: float | None = None,
    bottom_percent_hisp_pop: float | None = None,
    exclude_variables: Sequence[str] = (),
) -> PreparedRegressionData:
    """The regression sample, aligned: full feature matrix, targets and
    weights on the same kept rows, plus the group -> feature-names map for
    slicing per-group matrices.

    `feature_groups` holds real group slugs only: "full" is a runner
    concept, resolved before this function is called. The full-matrix
    baseline needs no entry here: it is the returned frame itself, unsliced.

    The kept rows are ALWAYS the rows complete on the FULL matrix and
    targets, whichever groups are being fit: subset runs must score on the
    same rows as full runs, or their R² values are not comparable.

    `exclude_variables` names predictors this level does not have, so the
    full matrix is the full matrix FOR THIS LEVEL -- pass
    `model_groups.TRACT_ABSENT_VARIABLES` to fit on tracts. It applies
    to the per-group matrices too, so a group and the full matrix cannot
    disagree about which columns exist.
    """
    feature_names_by_group = _feature_slugs_to_var_names(
        feature_groups, exclude_variables
    )

    full_feature_df = feature_frame(
        unfiltered_df, all_model_features(exclude_variables)
    )
    features_and_targets = pd.concat(
        [full_feature_df, unfiltered_df[list(REGRESSION_TARGETS)]], axis=1
    )
    complete_features = features_and_targets.notna().all(axis=1)
    if not complete_features.all():
        # The blame ledger: which columns cost which rows -- ex. 3,221 -> 2,913
        n_kept = int(complete_features.sum())
        print(
            f"complete cases: {n_kept:,} of {len(features_and_targets):,} "
            f"rows ({len(features_and_targets) - n_kept:,} dropped)"
        )
        missing_counts = features_and_targets.loc[~complete_features].isna().sum()
        for column, count in missing_counts.sort_values(ascending=False).items():
            if count > 0:
                print(f"  missing {column}: {int(count):,} rows")
    if top_percent_hisp_pop is not None or bottom_percent_hisp_pop is not None:
        rows_to_keep = _filter_top_or_bottom(
            df=unfiltered_df,
            full_features_to_keep=complete_features,
            top_percent_hisp_pop=top_percent_hisp_pop,
            bottom_percent_hisp_pop=bottom_percent_hisp_pop,
        )
    else:
        rows_to_keep = complete_features

    kept_rows = full_feature_df.index[rows_to_keep]
    return PreparedRegressionData(
        full_feature_df=full_feature_df.loc[kept_rows],
        targets_df=unfiltered_df.loc[kept_rows, list(REGRESSION_TARGETS)],
        hispanic_weights=unfiltered_df.loc[kept_rows, WEIGHT_COL],
        feature_names_by_group=feature_names_by_group,
    )


def _feature_slugs_to_var_names(
    feature_groups_slugs: list[ModelGroupName],
    exclude_variables: Sequence[str] = (),
) -> dict[ModelGroupName, list[str]]:
    """Group slug -> that group's predictor column names, in group order."""
    return {
        slug: group_features([slug], exclude_variables) for slug in feature_groups_slugs
    }


def describe_sample(
    top_percent: float | None,
    bottom_percent: float | None,
    n_rows: int,
    geography: str = "rows",
) -> tuple[str, str]:
    """Name the stratum a run was fit on, for titles and output paths.

    Shared by every driver so two runs on the same stratum always label
    themselves identically.

    Parameters
    ----------
    top_percent, bottom_percent : float or None
        The stratum arguments passed to `prepare_df_for_regression`; at
        most one is set.
    n_rows : int
        How many rows the prepared sample actually kept.
    geography : str
        What the rows ARE, from `config.describe_geography` -- "California
        tracts", "US counties". A figure gets read far from the folder it
        came out of, and "all complete-case rows" leaves a reader guessing
        which build and which level produced it. The bare "rows" default
        is a fallback, not something a driver should rely on.

    Returns
    -------
    tuple of (str, str)
        Human-readable sample note, and the suffix for an output directory
        name ("" for the unstratified sample).
    """
    if top_percent is not None:
        stratum = f"top {top_percent:g}% of {geography} by Hispanic population"
        suffix = f"_top-{top_percent:g}pct"
    elif bottom_percent is not None:
        stratum = f"bottom {bottom_percent:g}% of {geography} by Hispanic population"
        suffix = f"_bottom-{bottom_percent:g}pct"
    else:
        stratum, suffix = f"all complete-case {geography}", ""
    return f"{stratum} (n={n_rows:,})", suffix


def _filter_top_or_bottom(
    df: pd.DataFrame,
    full_features_to_keep: pd.Series,
    top_percent_hisp_pop: float | None = None,
    bottom_percent_hisp_pop: float | None = None,
) -> pd.Series:
    """Shrink the kept rows to one stratum by Hispanic population.

    `top_percent_hisp_pop=10` keeps rows AT OR ABOVE the 90th percentile;
    `bottom_percent_hisp_pop=90` keeps rows BELOW it -- the same cutoff,
    so the two runs partition the kept rows exactly.
    """
    hispanic_counts = df.loc[full_features_to_keep, WEIGHT_COL]
    if top_percent_hisp_pop is not None:
        cutoff = hispanic_counts.quantile(1 - top_percent_hisp_pop / 100)
        rows_to_keep = (df[WEIGHT_COL] >= cutoff) & full_features_to_keep
    elif bottom_percent_hisp_pop is not None:
        cutoff = hispanic_counts.quantile(bottom_percent_hisp_pop / 100)
        rows_to_keep = (df[WEIGHT_COL] < cutoff) & full_features_to_keep
    else:
        rows_to_keep = full_features_to_keep
    return rows_to_keep
