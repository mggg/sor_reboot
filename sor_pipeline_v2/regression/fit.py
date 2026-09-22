"""Fit and score ONE regression: (matrix, target, model, weighting, seed) -> metrics.

The three peer estimators and the harness that runs one of them once. Every
regression in the pipeline -- full matrix or a feature group, any seed --
goes through `fit_one`, so no two runs can differ in anything except what
they were asked to differ in.

Estimator configurations are untuned on purpose: a tuned LightGBM against
an untuned RF would measure the tuning, not the model family.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from model_utils.split import split_train_test
from regression.run_config import RegressionParameters

# Model key -> the label written in every output table and directory name.
MODEL_LABELS = {"rf": "random_forest", "lgbm": "lightgbm", "ridge": "ridge"}


def make_regressor(model: str, seed: int, params: RegressionParameters | None = None):
    """Construct one of the three peer estimators -- the single source of truth.

    "rf": the pipeline's forest, `n_estimators` trees capped at `max_depth`.
    "lgbm": gradient boosting configured to mirror the forest's restraint
        rather than to win -- same tree count and depth cap, a leaf cap
        (default 31 binds before depth 8 would), untuned learning rate;
        deterministic + force_row_wise make a seed exactly reproducible
        under n_jobs=-1.
    "ridge": StandardScaler + RidgeCV over a wide alpha grid -- the linear
        baseline. Not affected by the tree hyperparameters (its penalty is
        chosen by CV). Dense main effects, no link function: predictions can
        leave [0, 1], acceptable for an R² baseline, not for producing
        predicted shares.

    `params=None` means the RegressionParameters defaults.
    """
    p = params if params is not None else RegressionParameters()

    if model == "rf":
        return RandomForestRegressor(
            n_estimators=p.n_estimators,
            max_depth=p.max_depth,
            random_state=seed,
            n_jobs=-1,
        )
    if model == "lgbm":
        return LGBMRegressor(
            n_estimators=p.n_estimators,
            num_leaves=p.num_leaves,
            max_depth=p.max_depth,
            learning_rate=p.learning_rate,
            random_state=seed,
            deterministic=True,
            force_row_wise=True,
            n_jobs=-1,
            verbosity=-1,
        )
    if model == "ridge":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                ("regressor", RidgeCV(alphas=np.logspace(-3, 3, 100))),
            ]
        )
    raise ValueError(f"unknown model {model!r}; expected one of {list(MODEL_LABELS)}")


@dataclass(frozen=True)
class RegressionFitMetrics:
    """The scored result of one (matrix, target, model, weighting, seed) fit."""

    model: str
    weighting: str
    seed: int
    r2: float
    rmse: float
    n: int
    n_test: int
    # Effective sample size of the test fold: n_test when unweighted, else
    # (Σw)²/Σw². Travels with every weighted score because a weighted R²
    # quoted without it looks as solid as an unweighted one and is not.
    ess: float
    # The CV-chosen ridge penalty (NaN for the tree models), so a ridge row
    # is reproducible from its CSV.
    alpha: float


def split_fit_and_score_regression(
    X: pd.DataFrame,
    y: pd.Series,
    model: str,
    seed: int,
    weights: pd.Series | None = None,
    params: RegressionParameters | None = None,
) -> RegressionFitMetrics:
    """Split, fit, score -- the metrics of one fit.

    `weights` (aligned to X's index; pass the HISPANIC counts) switches the
    run from a question about PLACES to a question about PEOPLE, and is
    applied everywhere that has to agree:

      1. the fit     (sample_weight -- for the ridge, BOTH pipeline steps:
                      weighted scaling and weighted least squares)
      2. the scoring (R²/RMSE with the same test weights -- otherwise you
                      train on people and grade on counties)

    """
    X_train, X_test, y_train, y_test = split_train_test(X, y, seed)
    w_train = None if weights is None else weights.loc[X_train.index].to_numpy()
    w_test = None if weights is None else weights.loc[X_test.index].to_numpy()
    ess = (
        len(y_test)
        if w_test is None
        else float(
            w_test.sum() ** 2 / (w_test**2).sum()
        )  # ess calculated as \frac{(\sum w_i)^2}{\sum w_i^2}$$
    )

    estimator = make_regressor(model, seed, params=params)
    if model == "ridge":
        fit_params = (
            {}
            if w_train is None
            else {"scaler__sample_weight": w_train, "regressor__sample_weight": w_train}
        )
        estimator.fit(X_train, y_train, **fit_params)
    else:
        estimator.fit(X_train, y_train, sample_weight=w_train)
    y_pred = estimator.predict(X_test)

    return RegressionFitMetrics(
        model=MODEL_LABELS[model],
        weighting="unweighted" if weights is None else "weighted",
        seed=seed,
        r2=r2_score(y_test, y_pred, sample_weight=w_test),
        rmse=float(np.sqrt(mean_squared_error(y_test, y_pred, sample_weight=w_test))),
        n=len(y),
        n_test=len(y_test),
        ess=ess,
        alpha=(
            float(estimator.named_steps["regressor"].alpha_)
            if model == "ridge"
            else float("nan")
        ),
    )
