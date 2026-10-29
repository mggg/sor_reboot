"""Reconstruction test: how much of one feature is already in the others?

The removal test (`regression.substitution`) asks what the MODEL does
without a feature. This asks a prior question about the DATA: can the rest
of the matrix rebuild the column at all? Regressing a feature on every
other feature -- out of fold, with the same estimator and folds the model
uses -- gives the nonlinear analogue of a variance-inflation diagnostic.

The ceiling R2 says how redundant the column is. The curve says what KIND
of redundancy it is, and that distinction is the point:

  * a steep first step then flat -> the feature is a PROXY: one other
    column already carries it;
  * a gradual climb over several features -> the signal is DIFFUSE, spread
    thinly, and no single feature substitutes for it;
  * a low ceiling -> the column is genuinely its own measurement.

Contributors are chosen by GREEDY FORWARD SELECTION: at each step the
feature that adds the most out-of-fold R2 is taken. That makes each
step's gain meaningful -- a feature whose signal an earlier pick already
supplied adds nothing and is passed over -- and it names the specific
features that carry the column, which a count of features cannot.

The candidate pool is every feature scored INDIVIDUALLY first, keeping
the best predictors. An earlier version shortlisted by correlation
instead, and that hid genuinely predictive features: CUBANORIGIN
correlates 0.30 with HISPEDULTHS (44th of 94) yet alone predicts it
better than all but five features, because correlation only sees
straight-line relationships while the model does not. Screening on
predictive power costs one extra scan and removes that blind spot.

Run: `python -m regression.reconstruct --feature VAR_NAME
[--model rf|lgbm] [--exclude G ...] [--top-percent X | --bottom-percent X]`.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sklearn.metrics import r2_score

from build_dataset.model_groups import ModelGroupName, group_features
from regression.reconstruct.figures import plot_curve, plot_solo_versus_added
from regression.shared.cross_val import DEFAULT_FOLDS, out_of_fold_predictions
from regression.shared.prepare_df import describe_sample, prepare_df_for_regression
from utils import config

# Greedy search is quadratic in the candidate pool, so it runs over the
# best solo predictors rather than all features; the ceiling is still
# measured on the full set.
SHORTLIST = 25
GREEDY_STEPS = 8


def reconstruction_curve(
    feature: str,
    model_name: str = "rf",
    seed: int = 1,
    folds: int = DEFAULT_FOLDS,
    top_percent: float | None = None,
    bottom_percent: float | None = None,
    exclude_groups: list[ModelGroupName] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Rebuild `feature` from the other features, with 1..all contributors.

    Parameters
    ----------
    feature : str
        The column to reconstruct; must be in the model matrix.
    model_name : str
        A `make_regressor` key: "rf", "lgbm" or "ridge".
    seed : int
        Seeds the folds and the estimators.
    folds : int
        Cross-validation folds.
    top_percent, bottom_percent : float or None
        Restrict to one Hispanic-population stratum.
    exclude_groups : list of ModelGroupName or None
        Drop these groups first, to match the matrix a model run used.

    Returns
    -------
    tuple of (pandas.DataFrame, dict)
        The curve -- one row per k with the newest feature, its absolute
        correlation and the reconstruction R2 -- and a summary dict.

    Raises
    ------
    KeyError
        If `feature` is not a column of the prepared matrix.
    """
    unfiltered_df = pd.read_parquet(config.PROCESSED_NATIONAL_COUNTIES_PARQUET)
    prepared = prepare_df_for_regression(
        feature_groups=[],
        unfiltered_df=unfiltered_df,
        top_percent_hisp_pop=top_percent,
        bottom_percent_hisp_pop=bottom_percent,
    )
    X = prepared.full_feature_df
    if exclude_groups:
        gone = {c for g in exclude_groups for c in group_features([g])}
        kept = [c for c in X.columns if c not in gone]
        ablated = X[kept]
        X = ablated
    if feature not in X.columns:
        raise KeyError(
            f"{feature!r} is not a model feature; e.g. {list(X.columns[:3])}"
        )

    weights = prepared.hispanic_weights
    y = X[feature]
    others = X.drop(columns=[feature])
    abs_corr_by_feature = {
        str(name): float(value) for name, value in others.corrwith(y).abs().items()
    }

    def reconstruction_r2(columns: list[str]) -> float:
        """Out-of-fold R2 rebuilding `feature` from exactly these columns."""
        subset = others[columns]
        return float(
            r2_score(
                y,
                out_of_fold_predictions(model_name, subset, y, weights, folds, seed),
                sample_weight=weights,
            )
        )

    # Score every feature alone, and shortlist by that rather than by
    # correlation -- see the module docstring for why correlation misleads.
    # Keep the plain dict as well: Series[...] indexing returns a union the
    # type checker cannot narrow, and these are looked up by name below.
    solo_scores = {str(name): reconstruction_r2([str(name)]) for name in others.columns}
    solo = pd.Series(solo_scores).sort_values(ascending=False)
    shortlist = [str(name) for name in solo.head(SHORTLIST).index]
    print(f"  best solo predictor: {solo.index[0]} (R2 {solo.iloc[0]:.3f})")

    chosen: list[str] = []
    rows = []
    best_so_far = 0.0
    for step in range(1, GREEDY_STEPS + 1):
        scored = [
            (reconstruction_r2([*chosen, candidate]), candidate)
            for candidate in shortlist
            if candidate not in chosen
        ]
        if not scored:
            break
        r2, winner = max(scored)
        rows.append(
            {
                "step": step,
                "feature": winner,
                "solo_r2": solo_scores[winner],
                "abs_corr": abs_corr_by_feature[winner],
                "cumulative_r2": float(r2),
                "marginal_gain": float(r2 - best_so_far),
            }
        )
        chosen.append(winner)
        best_so_far = r2
        print(f"  step {step}: +{winner} -> R2 {r2:.3f}")

    curve = pd.DataFrame(rows)
    ceiling_r2 = reconstruction_r2(list(others.columns))

    first, ceiling = curve.cumulative_r2.iloc[0], float(ceiling_r2)
    summary = {
        "feature": feature,
        "n_other_features": others.shape[1],
        "best_single": str(solo.index[0]),
        "r2_best_single": float(solo.iloc[0]),
        "chosen": list(curve.feature),
        "r2_from_one": float(first),
        "r2_ceiling": float(ceiling),
        # How much of the recoverable signal the single best feature gets:
        # near 1 means a proxy, well below means the signal is diffuse.
        "share_from_one": float(first / ceiling) if ceiling > 0 else float("nan"),
        "sample": describe_sample(
            top_percent,
            bottom_percent,
            len(X),
            geography=config.describe_geography_in_eng("national_counties"),
        )[0]
        + (f", without {', '.join(exclude_groups)}" if exclude_groups else ""),
    }
    return curve, summary


def run_reconstruction(
    feature: str,
    model_name: str = "rf",
    seed: int = 1,
    folds: int = DEFAULT_FOLDS,
    top_percent: float | None = None,
    bottom_percent: float | None = None,
    exclude_groups: list[ModelGroupName] | None = None,
) -> Path:
    """Run the test, print the curve and verdict, write the CSV and figure."""
    curve, summary = reconstruction_curve(
        feature, model_name, seed, folds, top_percent, bottom_percent, exclude_groups
    )
    print(f"\nreconstructing {summary['feature']} — {model_name}, weighted")
    print(f"sample: {summary['sample']}\n")
    print("\n" + curve.to_string(index=False, float_format="%.3f"))

    share = summary["share_from_one"]
    verdict = (
        f"PROXY — the single best feature ({summary['best_single']}) already "
        f"carries {share:.0%} of what all of them recover"
        if share >= 0.8
        else (
            f"DIFFUSE — the best single feature ({summary['best_single']}) gets only "
            f"{share:.0%} of the recoverable signal; it takes several"
            if summary["r2_ceiling"] >= 0.5
            else "DISTINCT — the other features cannot rebuild this column"
        )
    )
    print(
        f"\nR² from one feature {summary['r2_from_one']:.3f} -> "
        f"ceiling {summary['r2_ceiling']:.3f}"
    )
    print(f"verdict: {verdict}")

    output_dir = (
        config.DATA_DIR
        / "prediction"
        / "regression"
        / f"reconstruct_{datetime.now(UTC).astimezone().date()}_{model_name}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    curve.to_csv(output_dir / f"reconstruct_{feature}.csv", index=False)
    plot_curve(curve, summary, output_dir / f"reconstruct_{feature}.png")
    plot_solo_versus_added(
        curve, summary, output_dir / f"reconstruct_{feature}_alone-vs-added.png"
    )
    print(f"\noutput -> {output_dir}")
    return output_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m regression.reconstruct",
        description="How much of one feature do the other features already carry?",
    )
    parser.add_argument("--feature", required=True, metavar="VAR_NAME")
    parser.add_argument("--model", choices=["rf", "lgbm", "ridge"], default="rf")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--folds", type=int, default=DEFAULT_FOLDS)
    parser.add_argument("--top-percent", type=float, default=None, metavar="X")
    parser.add_argument("--bottom-percent", type=float, default=None, metavar="X")
    parser.add_argument("--exclude", nargs="+", default=None, metavar="G")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_reconstruction(
        feature=args.feature,
        model_name=args.model,
        seed=args.seed,
        folds=args.folds,
        top_percent=args.top_percent,
        bottom_percent=args.bottom_percent,
        exclude_groups=args.exclude,
    )
