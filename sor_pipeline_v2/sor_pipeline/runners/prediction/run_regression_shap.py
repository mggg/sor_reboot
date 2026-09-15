from __future__ import annotations

import pandas as pd

from ...utils import config
from ...analysis import modeling, report

# Within-Hispanic proportion targets shared by the regression-family runners
# (RF+SHAP here; the alternative-regressor runner imports this list).
REGRESSION_TARGETS = [
    "Hisp SOR Alone PL Percent",
    "Hisp White SOR PL Percent",
    "Hisp White Alone PL Percent",
    "Hisp White PL Percent",
]


def run_regression_shap(df_reg: pd.DataFrame, X_reg: pd.DataFrame) -> None:
    """RF regression on within-Hispanic proportions + SHAP importances.

    `df_reg` must carry race percentages recomputed with denominator="HISPANIC";
    the driver preps it once and shares it across the regression-family runners.
    """
    config.REGRESSION_DIR.mkdir(parents=True, exist_ok=True)

    reg_metrics, importances, fig_paths = [], {}, {}
    for target in REGRESSION_TARGETS:
        print(f"\n===== {target} =====")
        m, comp, figs = modeling.run_rf_regression_shap(
            df_reg, target, X_reg, save_dir=config.REGRESSION_DIR
        )
        reg_metrics.append(m)
        importances[target] = comp
        fig_paths[target] = figs

    # Save metrics + per-feature importances as CSVs.
    metrics_all = pd.DataFrame(reg_metrics)
    shap_all = pd.concat(
        [c.assign(target=t) for t, c in importances.items()], ignore_index=True
    )
    metrics_all.to_csv(config.REGRESSION_METRICS_PATH, index=False)
    shap_all.to_csv(config.REGRESSION_SHAP_PATH, index=False)
    print(f"  wrote regression metrics -> {config.REGRESSION_METRICS_PATH}")
    print(f"  wrote SHAP importances -> {config.REGRESSION_SHAP_PATH}")

    # Section README: fit table + per-target figures and importance table.
    readme = config.REGRESSION_DIR / "README.md"
    intro = (
        "Random-forest regression predicting each within-Hispanic race-choice "
        "proportion (denominator = HISPANIC) from the covariates, with SHAP "
        "importances. Each target section shows the RF-vs-SHAP importance bar "
        "chart, the SHAP beeswarm summary, and a per-feature importance table. "
        "Features prefixed `log_` were log1p-transformed.\n"
    )
    metrics_block = (
        "## Model fit (R² / RMSE on held-out test set)\n\n"
        + report.df_to_md(metrics_all.set_index("target"), index_label="target")
    )
    sections = []
    for target in REGRESSION_TARGETS:
        sections.append(
            f"## {target}\n\n"
            + report.embed_figures(fig_paths[target], readme.parent)
            + "\n\n### Feature importances (RF vs SHAP)\n\n"
            + report.df_to_md(importances[target].set_index("Feature"), index_label="feature")
        )
    data_files = (
        "## Data files\n\n"
        "- [`metrics.csv`](metrics.csv)\n"
        "- [`shap_importance.csv`](shap_importance.csv)\n"
    )
    body = (
        intro + "\n" + metrics_block + "\n\n" + "\n\n".join(sections) + "\n\n" + data_files
    )
    report.write_section_readme(readme, "RF regression + SHAP", body)
    print(f"  wrote section summary -> {readme}")
