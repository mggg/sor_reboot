"""The one train/test split policy, shared by every model in the pipeline.

A single function so that for a given seed, every (model, weighting, group)
combination is scored on the identical held-out counties -- that pairing is
what makes their scores comparable. Any fit that split its own way would
quietly stop being part of the comparison.

County-level only for now: a plain random 80/20. When tracts arrive this is
where the group-aware split goes (tracts within a county are not independent;
a random tract split lets the model partially memorize county effects and
flatters the test R²) -- one function, so every fit inherits the fix at once.
"""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split


def split_train_test(
    X: pd.DataFrame, y: pd.Series, seed: int, test_size: float = 0.2
):
    """Random 80/20 split; returns (X_train, X_test, y_train, y_test).

    The exact call and argument order are load-bearing: the folds a seed
    produces depend on them, so changing either silently redraws every
    historical split.
    """
    return train_test_split(X, y, test_size=test_size, random_state=seed)
