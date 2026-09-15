"""Entry point: read the processed dataset, write the report tables."""

from __future__ import annotations

import pandas as pd

from feature_report.reliability import feature_reliability
from feature_report.stats import feature_stats
from utils import config


def report_counties() -> None:
    data_dir = config.DATA_DIR / "national_counties"
    df = pd.read_parquet(data_dir / "processed.parquet")
    raw = pd.read_parquet(data_dir / "raw.parquet")

    out_dir = data_dir / "report"
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = feature_stats(df)
    stats.to_csv(out_dir / "feature_stats.csv", index=False)
    print(f"wrote {len(stats)} features -> {out_dir / 'feature_stats.csv'}")

    reliability = feature_reliability(raw)
    reliability.to_csv(out_dir / "feature_reliability.csv", index=False)
    print(
        f"wrote {len(reliability)} features -> {out_dir / 'feature_reliability.csv'}"
    )
    # explorer.html regenerates separately (`python -m feature_report.explorer`):
    # it depends on the reliability table written above, so it stays an
    # explicit step rather than part of every report run.


if __name__ == "__main__":
    report_counties()
