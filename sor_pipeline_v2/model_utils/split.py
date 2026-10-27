"""The one train/test split policy, shared by every model in the pipeline."""

from __future__ import annotations

from typing import Literal, cast

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split

# Which rows the 80/20 train/test split keeps together. The rows are
# tracts either way; only the grouping changes.
# "none": every tract goes to train or test independently.
# "county": all of a county's tracts go to the same side, so the model is
# trained and scored on different counties. Tract data only -- in county
# data every row already is its own county.
SplitGrouping = Literal["none", "county"]


def county_groups(geoids: pd.Series) -> pd.Series:
    """Tract GEOID -> its 5-digit county code (state + county FIPS)."""
    return geoids.astype(str).str[:5]


def split_train_test(
    X: pd.DataFrame,
    y: pd.Series,
    seed: int,
    test_size: float = 0.2,
    groups: pd.Series | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """80/20 split; returns (X_train, X_test, y_train, y_test).

    Random over rows by default. With `groups` (aligned to X's index),
    whole groups go to one side, and `test_size` is then the share of
    GROUPS held out, not of rows -- so the test set's row count varies
    from seed to seed.
    """
    if groups is None:
        # sklearn's stubs type the result as a bare list; with a DataFrame
        # and a Series in, it is two of each.
        return cast(
            tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series],
            tuple(train_test_split(X, y, test_size=test_size, random_state=seed)),
        )
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_rows, test_rows = next(splitter.split(X, y, groups=groups.loc[X.index]))
    return X.iloc[train_rows], X.iloc[test_rows], y.iloc[train_rows], y.iloc[test_rows]
