"""Column selection for a model matrix, drift-checked against the frame."""

from __future__ import annotations

import pandas as pd


def feature_frame(
    df: pd.DataFrame,
    features: list[str],
) -> pd.DataFrame:
    """The feature columns of `df`, in the given order. Columns only, all rows.

    `features` is always explicit -- pass `feature_manifest.all_model_features()`
    for the full matrix, or e.g. `feature_manifest.group_features(["mobility"])`.
    """
    wanted = list(features)
    absent = [c for c in wanted if c not in df.columns]
    if absent:
        raise KeyError(
            f"{len(absent)} requested feature(s) not in the frame, first few: "
            f"{absent[:5]}. The frame and the feature manifest have drifted apart -- "
            "was this built from the current processed.parquet?"
        )
    return df[wanted]
