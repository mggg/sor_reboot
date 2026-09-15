"""Per-feature descriptive statistics, organized by model group."""

from __future__ import annotations

import pandas as pd
from build_dataset import manifest


def feature_stats(df: pd.DataFrame) -> pd.DataFrame:
    """One row per model feature: where it sits, its spread, and its gaps.

    Rows follow MODEL_GROUPS order (group A first, features in declaration
    order), so the table reads like the manifest with numbers attached.
    """
    rows = []
    for letter, (slug, _title, names) in manifest.MODEL_GROUPS.items():
        for name in names:
            values = df[name]
            rows.append(
                {
                    "group": letter,
                    "slug": slug,
                    "feature": name,
                    "mean": values.mean(),
                    "sd": values.std(),
                    "min": values.min(),
                    "median": values.median(),
                    "max": values.max(),
                    "n_missing": int(values.isna().sum()),
                    "pct_missing": round(100 * values.isna().mean(), 2),
                }
            )
    return pd.DataFrame(rows)
