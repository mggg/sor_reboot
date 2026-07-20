from __future__ import annotations
from ...utils import config
from ...ingest import census_api, geometry, election, store
from ...clean import merge, features
from ...analysis import viz, report, logistic
import pandas as pd


def run_univariate_logistic_regressions(df: pd.DataFrame) -> None:
    """Run univariate logistic regressions"""
    config.write_run_readme()  # ensure the run dir exists and records its params
    config.NATIONAL_LOGISTIC_DIR.mkdir(parents=True, exist_ok=True)
    logit_table = logistic.univariate_logistic(df)
    logit_table.to_csv(config.LOGISTIC_PATH, index=False)
    coef_matrix = logistic.coefficient_matrix(logit_table)
    print("Univariate logistic coefficients (covariate x dominant-race target):")
    print(coef_matrix.round(3))
    print(f"  wrote univariate logistic -> {config.LOGISTIC_PATH}")

    # Full statsmodels summaries (verbatim, notebook parity).
    summaries_path = config.NATIONAL_LOGISTIC_DIR / "summaries.txt"
    summaries_path.write_text(logistic.summary_report(df))
    print(f"  wrote full summaries -> {summaries_path}")

    # Forest plot of coefficients (±95% CI), one panel per dominant-race target.
    coef_fig = config.NATIONAL_LOGISTIC_DIR / "coefficients.png"
    viz.plot_logistic_coefficients(logit_table, save_path=coef_fig)
    print(f"  wrote coefficient plot -> {coef_fig}")

    readme = config.NATIONAL_LOGISTIC_DIR / "README.md"
    body = (
        "Each covariate **alone** vs. a binary dominant-race indicator "
        "(`Most_SOR` / `Most_White_SOR` / `Most_White`) — one single-predictor "
        "logistic regression per pair, with an intercept. Count covariates are "
        "log-transformed on strictly positive rows; the rest are used as-is. The "
        "matrix below shows coefficients; full per-model stats (std err, z, "
        "p-value, pseudo-R²) are in "
        "[`logistic.csv`](logistic.csv), and the complete "
        "statsmodels summaries (intercepts, confidence intervals, log-likelihood) "
        "are in [`summaries.txt`](summaries.txt).\n\n"
        "## Coefficient forest plot\n\n"
        + report.embed_figures([coef_fig], readme.parent)
        + "\n\n## Logistic coefficients (covariate x dominant-race target)\n\n"
        + report.df_to_md(coef_matrix, index_label="covariate")
    )
    report.write_section_readme(readme, "Univariate logistic regression", body)
    print(f"  wrote section summary -> {readme}")
