"""The model matrix: from the processed dataset to the X a model can fit on.

Two separable decisions live here, and they are kept as separate functions
because different runs combine them differently:

  WHICH COLUMNS -- `feature_frame`. The default is every model feature the
  manifest declares; any subset (one group, two groups, a hand-picked list)
  is just a different `features` argument. Requesting a column the frame
  does not carry raises immediately.

  WHICH ROWS -- `complete_rows`. Complete-case only: a row survives if every
  column in the matrix has a value. The blame ledger prints which features
  cost which counties, because "3,221 -> 2,913" with no explanation is how
  a silent Puerto Rico drop goes unnoticed.

`build_model_matrix` is the common path: columns, then rows, one call.

The group-isolation subtlety the two-function split exists for: isolation
runs must be COMPARABLE, so every group should fit on the SAME rows -- the
full matrix's complete cases -- not on each group's own complete cases
(a group with no missing data would otherwise fit on more counties than a
group with election features, and their R^2 would not be comparable). That
runner calls `feature_frame` + `complete_rows` on the FULL matrix once, then
slices group columns from the kept rows. A standalone fit on one group's own
complete cases is `build_model_matrix(df, features=...)` directly.
"""

from __future__ import annotations

import pandas as pd

from build_dataset import manifest


def feature_frame(
    df: pd.DataFrame,
    features: list[str] | None = None,
    level: str = "county",
) -> pd.DataFrame:
    """The feature columns of `df`, in manifest order. Columns only, all rows.

    `features=None` means the full matrix (`manifest.model_features`);
    otherwise pass any list -- e.g. `manifest.group_features(["D", "J"])`.
    """
    wanted = list(features) if features is not None else manifest.model_features(level)
    absent = [c for c in wanted if c not in df.columns]
    if absent:
        raise KeyError(
            f"{len(absent)} requested feature(s) not in the frame, first few: "
            f"{absent[:5]}. The frame and the manifest have drifted apart -- "
            "was this built from the current processed.parquet?"
        )
    return df[wanted]


def complete_rows(X: pd.DataFrame, verbose: bool = True) -> pd.Series:
    """Boolean mask of rows with a value in EVERY column of `X`.

    Prints the blame ledger: how many rows die, and which features are
    missing in the dying rows (a row usually lacks several at once, so the
    counts sum to more than the rows lost).
    """
    keep = X.notna().all(axis=1)  # includes rows with no missing values in any column
    if verbose and not keep.all():
        blame = (
            X.loc[~keep].isna().sum().sort_values(ascending=False)
        )  # count missing values per feature in rows that are not kept
        trimmed = {}
        for feature, count in blame.items():
            if count > 0:
                trimmed[feature] = count
        print(
            f"complete cases: {int(keep.sum()):,} of {len(X):,} rows "
            f"({len(X) - int(keep.sum()):,} dropped)"
        )
        for feature, n in trimmed.items():
            print(f"  missing {feature}: {int(n):,} rows")
    return keep


def build_model_matrix(
    df: pd.DataFrame,
    features: list[str] | None = None,
    level: str = "county",
    verbose: bool = True,
) -> pd.DataFrame:
    """Feature columns, complete cases: the X most fits start from.

    The returned index is the surviving rows of `df` -- align anything else
    (targets, weights) with `df.loc[X.index, ...]`, never by position.
    """
    X = feature_frame(df, features=features, level=level)
    return X.loc[complete_rows(X, verbose=verbose)]
