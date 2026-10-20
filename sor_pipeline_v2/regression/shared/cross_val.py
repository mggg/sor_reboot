"""Out-of-fold prediction: score every row from a model that never saw it.

Three drivers need this and none of them owns it. The residual driver ranks
counties by how far out of fold they land; the substitution and
reconstruction tests both compare out-of-fold R2 with and without a feature.
It lived in the residual driver until the three of them made that an
import from a sibling command.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from regression.shared.fit import fit_weighted, make_regressor

DEFAULT_FOLDS = 5


def out_of_fold_predictions(
    model_name: str,
    feature_df: pd.DataFrame,
    target_values: pd.Series,
    weights: pd.Series,
    folds: int,
    seed: int,
) -> pd.Series:
    """Predict every row from a model that never saw it.

    Parameters
    ----------
    model_name : str
        A `make_regressor` key: "rf", "lgbm" or "ridge".
    feature_df : pandas.DataFrame
        The full model matrix, one row per county.
    target_values : pandas.Series
        The target column, aligned to `feature_df`.
    weights : pandas.Series
        Per-county sample weights (the Hispanic counts), aligned to
        `feature_df`; applied to the fits exactly as the scored runs do.
    folds : int
        Number of cross-validation folds.
    seed : int
        Seeds both the fold shuffle and each estimator.

    Returns
    -------
    pandas.Series
        One prediction per county, aligned to `feature_df`'s index.
    """
    # A numpy accumulator, not a Series: the folds fill POSITIONS, and the
    # index is reattached once at the end.
    predictions = np.full(len(feature_df), np.nan)
    splitter = KFold(n_splits=folds, shuffle=True, random_state=seed)
    for fold, (train_rows, test_rows) in enumerate(splitter.split(feature_df), start=1):
        estimator = make_regressor(model_name, seed)
        fit_weighted(
            estimator,
            feature_df.iloc[train_rows],
            target_values.iloc[train_rows],
            weights.iloc[train_rows].to_numpy(),
        )
        # asarray: lightgbm's stubs type predict() as possibly sparse/tuple.
        predictions[test_rows] = np.asarray(
            estimator.predict(feature_df.iloc[test_rows])
        )
        print(f"  fold {fold}/{folds}: {len(train_rows)} fit, {len(test_rows)} scored")
    return pd.Series(predictions, index=feature_df.index)
