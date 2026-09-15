"""Driver: predictive modeling (was `nationhispanicraceprediction.ipynb`).

Reads the dataset produced by run_national, then runs dominant-race classification
and continuous-proportion regression (with SHAP). Each stage lives in its own
runner under runners/prediction/. Outputs are grouped under
data/prediction/{classification,regression}/, each holding its CSVs, figures, and a
README. Each step is checkpointed via `confirm_rerun`.

Run with:  python -m sor_pipeline.run_prediction
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless: figures save to files instead of opening a window

from sor_pipeline.utils import config, checkpoint
from sor_pipeline.ingest import store
from sor_pipeline.clean import features
from sor_pipeline.analysis import modeling, report
from sor_pipeline.runners.prediction.run_classification import run_classification
from sor_pipeline.runners.prediction.run_regression_shap import run_regression_shap
from sor_pipeline.runners.prediction.run_shap_dependence import run_shap_dependence
from sor_pipeline.runners.prediction.run_alternative_regressors import (
    run_alternative_regressors,
)
from sor_pipeline.runners.prediction.run_log_ratio import run_log_ratio


def _regression_frame():
    """Load the dataset with race percentages recomputed as within-Hispanic shares.

    Loaded fresh from disk (not reused from the classification step) because
    add_race_percentages overwrites the percentage columns in place.
    """
    df_reg = features.add_race_percentages(
        store.load(config.PARQUET_PATH), denominator="HISPANIC"
    )
    X_reg = modeling.build_model_features(df_reg, config.VARS_LOG, config.VARS_NO_LOG)
    return df_reg, X_reg


def main() -> None:
    config.PREDICTION_DIR.mkdir(parents=True, exist_ok=True)

    # --- Step 1: dominant-race classification (baseline / L1-logistic / random forest) ---
    if checkpoint.confirm_rerun(config.CLASSIFICATION_RF_PATH, "classification"):
        run_classification(store.load(config.PARQUET_PATH))

    # Steps 2-5 all model the within-Hispanic proportions; prep that frame once.
    df_reg, X_reg = _regression_frame()

    # --- Step 2: RF regression on within-Hispanic proportions + SHAP importances ---
    if checkpoint.confirm_rerun(config.REGRESSION_SHAP_PATH, "regression + SHAP"):
        run_regression_shap(df_reg, X_reg)

    # --- Step 3: SHAP dependence plots (explanatory feature interactions) ---
    if checkpoint.confirm_rerun(config.DEPENDENCE_DIR, "SHAP dependence"):
        run_shap_dependence(df_reg, X_reg)

    # --- Step 4: alternative regressors — polynomial + logit Lasso (6.C) ---
    if checkpoint.confirm_rerun(config.ALTERNATIVE_DIR, "alternative regressors"):
        run_alternative_regressors(df_reg, X_reg)

    # --- Step 5: log-ratio regression — RidgeCV + LassoCV (6.D) ---
    if checkpoint.confirm_rerun(config.LOGRATIO_DIR, "log-ratio regression"):
        run_log_ratio(df_reg, X_reg)

    # Top-level index for the prediction driver, linking its analyses.
    index = (
        "The predictive-modeling driver has two analyses:\n\n"
        "- [**Classification**](classification/README.md) — baseline / L1-logistic / "
        "random-forest classifiers for the dominant race choice.\n"
        "- [**Regression + SHAP**](regression/README.md) — random-forest regression on the "
        "within-Hispanic race-choice proportions, with SHAP importances plus "
        "[dependence](regression/dependence/README.md), "
        "[alternative regressors](regression/alternative/README.md), and "
        "[log-ratio](regression/log_ratio/README.md) sub-analyses.\n"
    )
    report.write_section_readme(
        config.PREDICTION_DIR / "README.md", "Predictive modeling", index
    )
    print(f"  wrote prediction index -> {config.PREDICTION_DIR / 'README.md'}")


if __name__ == "__main__":
    main()
