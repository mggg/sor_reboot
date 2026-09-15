from __future__ import annotations

import pandas as pd

from ...utils import config
from ...analysis import modeling, report
from .run_regression_shap import REGRESSION_TARGETS


def run_alternative_regressors(df_reg: pd.DataFrame, X_reg: pd.DataFrame) -> None:
    """Alternative regressors on the within-Hispanic proportions: polynomial + logit Lasso (6.C)."""
    config.ALTERNATIVE_DIR.mkdir(parents=True, exist_ok=True)

    poly = {t: modeling.run_polynomial_lasso(df_reg, t, X_reg) for t in REGRESSION_TARGETS}
    logit = {t: modeling.run_logit_lasso(df_reg, t, X_reg) for t in REGRESSION_TARGETS}

    metrics_all = pd.DataFrame(
        [{**m, "model": "poly_lasso"} for m, _ in poly.values()]
        + [{**m, "model": "logit_lasso"} for m, _ in logit.values()]
    )
    metrics_all.to_csv(config.ALTERNATIVE_DIR / "metrics.csv", index=False)
    pd.concat([c.assign(target=t) for t, (_, c) in poly.items()], ignore_index=True).to_csv(
        config.ALTERNATIVE_DIR / "poly_coefficients.csv", index=False
    )
    pd.concat([c.assign(target=t) for t, (_, c) in logit.items()], ignore_index=True).to_csv(
        config.ALTERNATIVE_DIR / "logit_coefficients.csv", index=False
    )
    print(f"  wrote alternative-regressor outputs -> {config.ALTERNATIVE_DIR}")

    readme = config.ALTERNATIVE_DIR / "README.md"
    body = (
        "Alternative regressors on the within-Hispanic proportions (the notebook flags "
        "these as lower-performing, kept for completeness):\n\n"
        "- **Polynomial Lasso** — degree-2 interaction-only features, L1-penalized so "
        "weak interactions drop to zero.\n"
        "- **Logit Lasso** — Lasso on the log-odds of the proportion (respects the [0,1] "
        "bound), inverted back to the proportion scale.\n\n"
        "## Model fit (held-out test set)\n\n"
        + report.df_to_md(metrics_all.set_index("model"), index_label="model")
        + "\n\n## Data files\n\n"
        "- [`metrics.csv`](metrics.csv)\n"
        "- [`poly_coefficients.csv`](poly_coefficients.csv)\n"
        "- [`logit_coefficients.csv`](logit_coefficients.csv)\n"
    )
    report.write_section_readme(readme, "Alternative regressors", body)
    print(f"  wrote section summary -> {readme}")
