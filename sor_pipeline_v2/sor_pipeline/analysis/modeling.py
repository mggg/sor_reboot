"""Predictive modeling: dominant-race classification and continuous-proportion regression.

Migrated from `nationhispanicraceprediction` cells 3-22. The notebook had several
duplicated cells (the logit-Lasso and polynomial-Lasso blocks appear twice); only
one copy of each is carried over here.
"""

from __future__ import annotations

from pathlib import Path

import shap
import matplotlib.pyplot as plt
from sor_pipeline.utils import config
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import r2_score, mean_squared_error, log_loss, accuracy_score
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegressionCV, Ridge, Lasso, LassoCV, RidgeCV
from sklearn.compose import TransformedTargetRegressor


def build_model_features(
    df: pd.DataFrame, vars_log: list[str], vars_no_log: list[str]
) -> pd.DataFrame:
    """Build the sklearn feature matrix: copy the no-log covariates, log1p the counts.

    log1p (log(1+x)) keeps zero-valued counts finite. Returns a feature-only frame
    aligned to ``df``'s rows; the modeling functions below pair it with a target.
    """
    X = df[vars_no_log].copy()
    for col in vars_log:
        X[f"log_{col}"] = np.log1p(df[col])
    return X


def run_classification_models(
    df: pd.DataFrame,
    target_col: str,
    X_features: pd.DataFrame,
    verbose: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit baseline / logistic / random-forest classifiers for one target.

    Builds the feature matrix, drops rows with NaNs in features or target,
    does an 80/20 train/test split (``random_state=42``), then fits and scores:
      * a naive baseline (predicts the training mean probability / majority class),
      * an L1-penalized LogisticRegressionCV inside a StandardScaler pipeline,
      * a depth-limited RandomForestClassifier.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing the features and target. Must include columns for the
        covariates and the binary target.
    target_col : str
        Binary target column (e.g. 'Most_SOR').
    verbose : bool, default True
        If True, print metrics and the feature-importance tables.

    Returns
    -------
    (metrics, importance_df, rf_importance_df) : tuple of pandas.DataFrame
        ``metrics`` holds train/test log loss + accuracy for the baseline, logistic,
        and random-forest models (indexed by model name); ``importance_df`` and
        ``rf_importance_df`` are the logistic coefficients and RF importances, each
        sorted by descending magnitude.
    """
    # Build features and align with the target, dropping incomplete rows
    y_target = df[target_col]
    model_data = pd.concat(
        [y_target, X_features], axis=1
    ).dropna()  # drop rows with NaN in target or features

    X = model_data.drop(columns=[target_col])
    y = model_data[target_col].astype(int)  # ensure binary

    # 80/20 train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=config.RANDOM_STATE, stratify=y
    )  # stratify=y ensures the train/test sets have the same class distribution as the original data (don't want to accidentally have all 1s in the train set and all 0s in the test set, for example).

    # --- Naive baseline: constant training-mean probability / majority class ---
    mean_prob = y_train.mean()
    majority_class = 1 if mean_prob >= 0.5 else 0
    base_train_proba = np.full(len(y_train), mean_prob)
    base_test_proba = np.full(len(y_test), mean_prob)
    base_train_pred = np.full(len(y_train), majority_class)
    base_test_pred = np.full(len(y_test), majority_class)

    # --- L1-regularized logistic regression (scaled, cross-validated) ---
    lr_pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "lr_cv",
                LogisticRegressionCV(
                    penalty="l1",
                    solver="saga",
                    cv=5,
                    max_iter=5000,
                    random_state=config.RANDOM_STATE,
                ),
            ),
        ]
    )
    lr_pipeline.fit(X_train, y_train)

    # --- Random forest (max_depth limited to curb overfitting) ---
    rf_model = RandomForestClassifier(
        n_estimators=100, max_depth=8, random_state=config.RANDOM_STATE
    )
    rf_model.fit(X_train, y_train)

    # --- Train/test metrics for all three models, as one returnable table ---
    def _metrics_row(name, tr_proba, te_proba, tr_pred, te_pred):
        return {
            "model": name,
            "train_log_loss": log_loss(y_train, tr_proba),
            "test_log_loss": log_loss(y_test, te_proba),
            "train_accuracy": accuracy_score(y_train, tr_pred),
            "test_accuracy": accuracy_score(y_test, te_pred),
        }

    metrics = pd.DataFrame(
        [
            _metrics_row(
                "Baseline",
                base_train_proba,
                base_test_proba,
                base_train_pred,
                base_test_pred,
            ),
            _metrics_row(
                "Logistic (L1-CV)",
                lr_pipeline.predict_proba(X_train),
                lr_pipeline.predict_proba(X_test),
                lr_pipeline.predict(X_train),
                lr_pipeline.predict(X_test),
            ),
            _metrics_row(
                "Random Forest",
                rf_model.predict_proba(X_train),
                rf_model.predict_proba(X_test),
                rf_model.predict(X_train),
                rf_model.predict(X_test),
            ),
        ]
    ).set_index("model")

    if verbose:
        print(f"--- {target_col}: model metrics ---")
        print(metrics.round(4))

    # --- Logistic-regression coefficients, sorted by absolute magnitude ---
    importance_df = pd.DataFrame(
        {
            "Feature": X_train.columns,
            "Coefficient": lr_pipeline.named_steps["lr_cv"].coef_[0],
        }
    )
    importance_df["Abs_Magnitude"] = importance_df["Coefficient"].abs()
    importance_df = importance_df.sort_values(by="Abs_Magnitude", ascending=False).drop(
        columns=["Abs_Magnitude"]
    )

    # --- Random-forest feature importances, sorted descending ---
    rf_importance_df = (
        pd.DataFrame(
            {"Feature": X_train.columns, "Importance": rf_model.feature_importances_}
        )
        .sort_values(by="Importance", ascending=False)
        .reset_index(drop=True)
    )

    if verbose:
        print("--- Logistic regression importance dataframe ---")
        print(importance_df.reset_index(drop=True))
        print("--- Random Forest importance dataframe ---")
        print(rf_importance_df)

    return metrics, importance_df, rf_importance_df


def _save_shap_figures(comparison_df, shap_values, X_test, target_col, save_dir):
    """Write the RF-vs-SHAP importance bar chart and the SHAP beeswarm; return their paths."""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    stem = target_col.replace(" ", "_")
    importance_path = save_dir / f"{stem}_importance.png"
    beeswarm_path = save_dir / f"{stem}_shap_summary.png"

    # Side-by-side bar chart: built-in RF importance vs normalized mean |SHAP|.
    x = np.arange(len(comparison_df))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(
        x - width / 2,
        comparison_df["RF_Importance"],
        width,
        label="Random Forest",
        color="skyblue",
    )
    ax.bar(
        x + width / 2,
        comparison_df["SHAP_Normalized"],
        width,
        label="SHAP mean |value| (normalized)",
        color="salmon",
    )
    ax.set_xlabel("Feature")
    ax.set_ylabel("Relative importance")
    ax.set_title(f"Feature importance: RF vs SHAP — {target_col}")
    ax.set_xticks(x)
    ax.set_xticklabels(comparison_df["Feature"], rotation=45, ha="right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(importance_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Classic SHAP beeswarm summary (per-observation feature effects).
    plt.figure()
    shap.summary_plot(shap_values, X_test, show=False)
    plt.title(f"SHAP summary — {target_col}", pad=20)
    plt.savefig(beeswarm_path, dpi=150, bbox_inches="tight")
    plt.close()

    return [importance_path, beeswarm_path]


def run_rf_regression_shap(
    df, target_col: str, X_features: pd.DataFrame, save_dir=None
):
    """Random-forest regression on a continuous proportion target, with SHAP importances.

    Fits a depth-limited RandomForestRegressor, scores it (R², RMSE), and computes
    global SHAP importances (mean |SHAP| per feature). When ``save_dir`` is given,
    writes two figures — an RF-vs-SHAP importance bar chart and the SHAP beeswarm.

    Returns
    -------
    (metrics, comparison_df, fig_paths) : (dict, pandas.DataFrame, list[Path])
        ``metrics`` = {"target", "r2", "rmse", "n"}; ``comparison_df`` holds per-feature
        RF importance, mean |SHAP|, and normalized SHAP, sorted by SHAP importance;
        ``fig_paths`` are the saved figures (empty when ``save_dir`` is None).
    """
    print(f"Training Random Forest Regressor for target: {target_col}...")

    # Align features with the target and drop incomplete rows
    model_data = pd.concat([X_features, df[target_col]], axis=1).dropna()
    X_t = model_data.drop(columns=[target_col])
    y_t = model_data[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X_t, y_t, test_size=0.2, random_state=config.RANDOM_STATE
    )

    # Depth limited to reduce overfitting (raising max_depth could be explored)
    rf_regressor = RandomForestRegressor(
        n_estimators=100, max_depth=8, random_state=config.RANDOM_STATE
    )
    rf_regressor.fit(X_train, y_train)

    # Evaluate on the held-out test set
    y_pred = rf_regressor.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    metrics = {"target": target_col, "r2": r2, "rmse": rmse, "n": len(model_data)}
    print(f"[{target_col}] R² = {r2:.4f} | RMSE = {rmse:.4f}")

    # Built-in RF importances + SHAP global importances (mean |SHAP| per feature)
    explainer = shap.TreeExplainer(rf_regressor)
    shap_values = explainer.shap_values(X_test)

    comparison_df = pd.DataFrame(
        {
            "Feature": X_train.columns,
            "RF_Importance": rf_regressor.feature_importances_,
            "SHAP_Importance": np.abs(shap_values).mean(axis=0),
        }
    )
    # Normalize SHAP to sum to 1 (RF importances already do), so the bars are comparable.
    comparison_df["SHAP_Normalized"] = (
        comparison_df["SHAP_Importance"] / comparison_df["SHAP_Importance"].sum()
    )
    comparison_df = comparison_df.sort_values(
        by="SHAP_Importance", ascending=False
    ).reset_index(drop=True)

    fig_paths = []
    if save_dir is not None:
        fig_paths = _save_shap_figures(
            comparison_df, shap_values, X_test, target_col, save_dir
        )

    return metrics, comparison_df, fig_paths


def shap_dependence_plots(df, target_col: str, X_features, pairs=None, save_dir=None):
    """SHAP dependence plots (explanatory) — how each feature's effect bends with another.

    Unlike ``run_rf_regression_shap`` (which splits + evaluates), this fits on the FULL
    data (no split; these are explanatory, not scored) and computes SHAP values ONCE,
    then draws one dependence plot per ``(feature, interaction_index)`` pair off that
    single computation.

    Parameters
    ----------
    pairs : list[tuple[str, str]] | None
        ``(feature, interaction)`` pairs. ``interaction`` is a column name or "auto"
        (SHAP picks the strongest interacting feature). Defaults to every feature with
        "auto" — the full exploratory pass.
    save_dir : path-like | None
        If given, each plot is written there; otherwise shown. Returns the saved paths.
    """
    model_data = pd.concat([X_features, df[target_col]], axis=1).dropna()
    X_t = model_data.drop(columns=[target_col])
    y_t = model_data[target_col]

    rf = RandomForestRegressor(
        n_estimators=100, max_depth=8, random_state=config.RANDOM_STATE
    ).fit(X_t, y_t)
    shap_values = shap.TreeExplainer(rf).shap_values(
        X_t
    )  # computed ONCE, reused per plot

    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

    pairs = pairs if pairs is not None else [(f, "auto") for f in X_t.columns]
    paths = []
    for feature, interaction in pairs:
        # dependence_plot builds its OWN figure — grab it with gcf() (don't pre-make one,
        # or you save an empty figure while shap draws on a different one).
        shap.dependence_plot(
            feature, shap_values, X_t, interaction_index=interaction, show=False
        )
        fig = plt.gcf()
        fig.set_size_inches(8, 5)
        title = f"SHAP dependence: {feature}"
        if interaction not in (None, "auto"):
            title += f"  ×  {interaction}"
        plt.title(title, pad=20)
        plt.grid(True, alpha=0.3)
        if save_dir is not None:
            tag = (
                feature
                if interaction in (None, "auto")
                else f"{feature}__x__{interaction}"
            )
            p = save_dir / f"dependence_{tag}.png"
            fig.savefig(p, dpi=150, bbox_inches="tight")
            plt.close(fig)
            paths.append(p)
        else:
            plt.show()
    return paths


def _sort_by_abs(coef_df):
    """Sort a Feature/Coefficient table by descending |Coefficient|."""
    order = coef_df["Coefficient"].abs().sort_values(ascending=False).index
    return coef_df.reindex(order).reset_index(drop=True)


def run_polynomial_lasso(df, target_col: str, X_features):
    """Degree-2 interaction-only Lasso on one proportion target (6.C).

    Generates pairwise interaction features, scales them (L1 needs comparable scales),
    fits Lasso (alpha=0.01), and reports the surviving non-zero coefficients with sign.
    Returns ``(metrics, coef_df)``: metrics = {target, r2, rmse, n_selected}; coef_df has
    Feature / Coefficient / Direction, sorted by magnitude.
    """
    model_data = pd.concat([X_features, df[target_col]], axis=1).dropna()
    X_t = model_data.drop(columns=[target_col])
    y_t = model_data[target_col]
    X_train, X_test, y_train, y_test = train_test_split(
        X_t, y_t, test_size=0.2, random_state=config.RANDOM_STATE
    )

    pipe = Pipeline(
        [
            (
                "poly",
                PolynomialFeatures(degree=2, interaction_only=True, include_bias=False),
            ),
            ("scaler", StandardScaler()),
            (
                "regressor",
                Lasso(alpha=0.01, max_iter=10000, random_state=config.RANDOM_STATE),
            ),
        ]
    ).fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    names = pipe.named_steps["poly"].get_feature_names_out(X_t.columns)
    coef_df = pd.DataFrame(
        {"Feature": names, "Coefficient": pipe.named_steps["regressor"].coef_}
    )
    coef_df = coef_df[
        coef_df["Coefficient"] != 0
    ].copy()  # keep features Lasso didn't zero out
    coef_df["Direction"] = np.where(
        coef_df["Coefficient"] > 0, "Positive (+)", "Negative (-)"
    )
    coef_df = _sort_by_abs(coef_df)
    metrics = {
        "target": target_col,
        "r2": r2_score(y_test, y_pred),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "n_selected": len(coef_df),
    }
    return metrics, coef_df


def _to_log_odds(p):
    """Map a proportion in [0,1] to the log-odds scale, clipped away from 0/1."""
    p = np.clip(np.asarray(p, dtype=float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def _from_log_odds(z):
    """Invert :func:`_to_log_odds`, returning a proportion in (0,1)."""
    return 1 / (1 + np.exp(-z))


def run_logit_lasso(df, target_col: str, X_features):
    """Lasso on the logit (log-odds) of a proportion target (6.C).

    Proportions are bounded in [0,1], which linear regression ignores; so we fit on the
    log-odds scale (via TransformedTargetRegressor) and invert predictions back. NOTE:
    the notebook divided the target by 100 (assuming a 0-100 percentage); our targets are
    0-1 fractions, so we logit the fraction directly. Returns ``(metrics, coef_df)``.
    """
    model_data = pd.concat([X_features, df[target_col]], axis=1).dropna()
    X_t = model_data.drop(columns=[target_col])
    y_t = model_data[target_col]
    X_train, X_test, y_train, y_test = train_test_split(
        X_t, y_t, test_size=0.2, random_state=config.RANDOM_STATE
    )

    lasso_pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "regressor",
                Lasso(alpha=0.01, max_iter=10000, random_state=config.RANDOM_STATE),
            ),
        ]
    )
    model = TransformedTargetRegressor(
        regressor=lasso_pipeline, func=_to_log_odds, inverse_func=_from_log_odds
    ).fit(X_train, y_train)

    y_pred = model.predict(X_test)
    coef_df = pd.DataFrame(
        {
            "Feature": X_t.columns,
            "Coefficient": model.regressor_.named_steps["regressor"].coef_,
        }
    )
    coef_df = coef_df[coef_df["Coefficient"] != 0].copy()
    coef_df = _sort_by_abs(coef_df)
    metrics = {
        "target": target_col,
        "r2": r2_score(y_test, y_pred),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "n_selected": len(coef_df),
    }
    return metrics, coef_df


# Log-ratio targets (6.D): each race choice vs. "any White identification" (Hisp White PL Percent).
LOG_RATIO_SPECS = [
    ("SORA_vs_White", "Hisp SOR Alone PL Percent"),
    ("WhiteSOR_vs_White", "Hisp White SOR PL Percent"),
    ("WhiteAlone_vs_White", "Hisp White Alone PL Percent"),
]


def run_log_ratio_regression(df, X_features, epsilon: float = 1e-5):
    """RidgeCV + LassoCV on log-ratios of each race choice vs 'any White identification' (6.D).

    Race proportions are compositional (they trade off), so instead of modeling each
    separately we model log(choice / any-White) — relative preference for the numerator
    over White. Each ratio is fit with both RidgeCV (L2) and LassoCV (L1), cross-validating
    the penalty. Returns ``(metrics_df, coef_tables)``: metrics_df has one row per
    (ratio, method) with alpha/r2/rmse; coef_tables maps (ratio, method) -> coef DataFrame.
    """
    white = df["Hisp White PL Percent"] + epsilon  # baseline anchor
    metrics_rows, coef_tables = [], {}

    for label, num_col in LOG_RATIO_SPECS:
        y_ratio = np.log((df[num_col] + epsilon) / white)
        model_data = pd.concat([X_features, y_ratio.rename("y")], axis=1).dropna()
        X_t = model_data.drop(columns=["y"])
        y_t = model_data["y"]
        X_train, X_test, y_train, y_test = train_test_split(
            X_t, y_t, test_size=0.2, random_state=config.RANDOM_STATE
        )

        methods = {
            "ridge": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("m", RidgeCV(alphas=np.logspace(-3, 3, 100))),
                ]
            ),
            "lasso": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "m",
                        LassoCV(
                            alphas=np.logspace(-5, 1, 100),
                            cv=5,
                            max_iter=10000,
                            random_state=config.RANDOM_STATE,
                        ),
                    ),
                ]
            ),
        }
        for method, pipe in methods.items():
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            m = pipe.named_steps["m"]
            metrics_rows.append(
                {
                    "ratio": label,
                    "method": method,
                    "alpha": float(m.alpha_),
                    "r2": r2_score(y_test, y_pred),
                    "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
                }
            )
            coef_df = pd.DataFrame({"Feature": X_t.columns, "Coefficient": m.coef_})
            if method == "lasso":
                coef_df = coef_df[
                    coef_df["Coefficient"] != 0
                ].copy()  # L1 zeros out weak ones
            coef_tables[(label, method)] = _sort_by_abs(coef_df)

    return pd.DataFrame(metrics_rows), coef_tables
