"""The one train/test split policy, shared by every model in the pipeline."""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split


def split_train_test(X: pd.DataFrame, y: pd.Series, seed: int, test_size: float = 0.2):
    """Random 80/20 split; returns (X_train, X_test, y_train, y_test)."""
    return train_test_split(X, y, test_size=test_size, random_state=seed)
