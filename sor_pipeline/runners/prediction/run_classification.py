from __future__ import annotations

import pandas as pd

from ...utils import config
from ...analysis import modeling, report

CLASSIFICATION_TARGETS = ["Most_SOR", "Most_White_SOR", "Most_White"]


def run_classification(df: pd.DataFrame) -> None:
    """Dominant-race classification: baseline / L1-logistic / random forest per target."""
    config.CLASSIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    X = modeling.build_model_features(df, config.VARS_LOG, config.VARS_NO_LOG)

    results = {}  # target -> (metrics df, logistic-coefficient df, rf-importance df)
    for target in CLASSIFICATION_TARGETS:
        print(f"\n===== {target} =====")
        results[target] = modeling.run_classification_models(df, target, X)

    # Save each table as one long-form CSV (a `target` column tags the rows).
    metrics_all = pd.concat(
        [m.reset_index().assign(target=t) for t, (m, _, _) in results.items()],
        ignore_index=True,
    )
    logit_all = pd.concat(
        [logit.assign(target=t) for t, (_, logit, _) in results.items()],
        ignore_index=True,
    )
    rf_all = pd.concat(
        [rf.assign(target=t) for t, (_, _, rf) in results.items()],
        ignore_index=True,
    )
    metrics_all.to_csv(config.CLASSIFICATION_METRICS_PATH, index=False)
    logit_all.to_csv(config.CLASSIFICATION_LOGIT_PATH, index=False)
    rf_all.to_csv(config.CLASSIFICATION_RF_PATH, index=False)
    print(f"  wrote model metrics -> {config.CLASSIFICATION_METRICS_PATH}")
    print(f"  wrote logistic importances -> {config.CLASSIFICATION_LOGIT_PATH}")
    print(f"  wrote RF importances -> {config.CLASSIFICATION_RF_PATH}")

    # Section README: per-target model metrics, logistic coefficients, RF importances.
    readme = config.CLASSIFICATION_DIR / "README.md"
    intro = (
        "Three classifiers per binary dominant-race target "
        "(`Most_SOR` / `Most_White_SOR` / `Most_White`): a naive baseline, an "
        "L1-regularized `LogisticRegressionCV` (scaled), and a depth-limited "
        "random forest. Each target section shows train/test log loss + accuracy "
        "for all three models, then the logistic coefficients and random-forest "
        "importances. Features prefixed `log_` were log1p-transformed.\n"
    )
    sections = []
    for target in CLASSIFICATION_TARGETS:
        metrics_df, logit_df, rf_df = results[target]
        sections.append(
            f"## {target}\n\n"
            "### Model metrics (train / test)\n\n"
            + report.df_to_md(metrics_df, index_label="model")
            + "\n\n### Logistic-regression coefficients\n\n"
            + report.df_to_md(logit_df.set_index("Feature"), index_label="feature")
            + "\n\n### Random-forest importances\n\n"
            + report.df_to_md(rf_df.set_index("Feature"), index_label="feature")
        )
    data_files = (
        "## Data files\n\n"
        "Machine-readable copies (long-form, all targets in one file):\n\n"
        "- [`metrics.csv`](metrics.csv)\n"
        "- [`logistic_importance.csv`](logistic_importance.csv)\n"
        "- [`rf_importance.csv`](rf_importance.csv)\n"
    )
    # Consolidated headline: one row per target, models side by side (test set).
    summary = pd.DataFrame(
        {
            t: {
                "baseline_acc": m.loc["Baseline", "test_accuracy"],
                "logistic_acc": m.loc["Logistic (L1-CV)", "test_accuracy"],
                "rf_acc": m.loc["Random Forest", "test_accuracy"],
                "rf_test_logloss": m.loc["Random Forest", "test_log_loss"],
            }
            for t, (m, _, _) in results.items()
        }
    ).T
    summary_block = (
        "## Summary — test accuracy vs. baseline\n\n"
        + report.df_to_md(summary, index_label="target")
    )
    body = (
        intro + "\n" + summary_block + "\n\n" + "\n\n".join(sections) + "\n\n" + data_files
    )
    report.write_section_readme(readme, "Dominant-race classification", body)
    print(f"  wrote section summary -> {readme}")
