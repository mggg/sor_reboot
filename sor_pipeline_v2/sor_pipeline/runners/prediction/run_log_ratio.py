from __future__ import annotations

import pandas as pd

from ...utils import config
from ...analysis import modeling, report


def run_log_ratio(df_reg: pd.DataFrame, X_reg: pd.DataFrame) -> None:
    """Log-ratio regression: RidgeCV + LassoCV on log(choice / any-White) (6.D)."""
    config.LOGRATIO_DIR.mkdir(parents=True, exist_ok=True)

    metrics_df, coef_tables = modeling.run_log_ratio_regression(df_reg, X_reg)
    metrics_df.to_csv(config.LOGRATIO_DIR / "metrics.csv", index=False)
    pd.concat(
        [c.assign(ratio=r, method=meth) for (r, meth), c in coef_tables.items()],
        ignore_index=True,
    ).to_csv(config.LOGRATIO_DIR / "coefficients.csv", index=False)
    print(f"  wrote log-ratio outputs -> {config.LOGRATIO_DIR}")

    readme = config.LOGRATIO_DIR / "README.md"
    body = (
        "Log-ratio regression: model `log(choice / any-White identification)` instead of "
        "each proportion alone, capturing *relative* preference (race proportions are "
        "compositional). Each ratio is fit with RidgeCV (L2) and LassoCV (L1), each "
        "cross-validating the penalty.\n\n"
        "## Model fit (held-out test set)\n\n"
        + report.df_to_md(metrics_df.set_index("ratio"), index_label="ratio")
        + "\n\n## Data files\n\n"
        "- [`metrics.csv`](metrics.csv)\n"
        "- [`coefficients.csv`](coefficients.csv)\n"
    )
    report.write_section_readme(readme, "Log-ratio regression", body)
    print(f"  wrote section summary -> {readme}")
