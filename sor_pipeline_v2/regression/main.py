"""The group-stability run: every (group x model x weighting x target) across seeds.

The question: how much does each theme -- language, citizenship, origin,
mobility, education, income, employment, household, racial composition,
geography, elections -- explain of Hispanic race choice ALONE? The full
matrix runs alongside as the baseline every group is read against.

Three guarantees keep the comparison honest:

1. ONE SAMPLE. Every group is fit on the rows complete on the FULL matrix
   and targets -- never on its own complete cases, which would hand each
   group a different county sample and make the R² incomparable.
2. PAIRED SPLITS. For a given seed every group, model and weighting is
   scored on the identical held-out counties (one split policy, seeded).
3. SEED SPREAD. Scores are repeated across seeds and reported mean ± sd,
   because a single split moves R² by more than many between-group gaps.

Reading rules: group R² values do NOT sum to the full-matrix R² (themes
share information), and a gap smaller than the sd column is seed noise.

Run: `python -m regression.main [--seeds LO HI] [--max-depth N]
[--n-estimators N] [--learning-rate F] [--num-leaves N] [--top-percent X]`.
Hyperparameter defaults live in fit.DEFAULT_PARAMS; the ridge ignores them
(its penalty is CV-chosen). `--top-percent 10` restricts the whole run to
the top 10% of complete-case counties by Hispanic population -- the
big-county stratum, where the weighted fits keep a usable effective sample
size. Outputs land in a per-run directory named by the
date, the seed range, and the hyperparameters, e.g.
`data/prediction/regression/2026-09-15_seeds-1-50_max-depth-8/`:
`group_metrics_by_seed.csv` (one row per fit), `group_summary.csv`
(mean ± sd per combination), and the comparison figure per target.
"""

from __future__ import annotations

import argparse
import time
from datetime import date

import pandas as pd
from build_dataset import manifest
from model_utils.matrix import feature_frame
from utils import config

from regression import figures
from regression.fit import DEFAULT_PARAMS, MODEL_LABELS, fit_one
from regression.regression_utils import FULL, TARGETS, WEIGHT_COL


def _run_dir(
    seeds: list[int],
    params: dict,
    top_percent: float | None = None,
    groups: list[str] | None = None,
) -> config.Path:
    """`<date>_seeds-<lo>-<hi>_max-depth-<d>[_<param>-<v> for non-defaults]`.

    The seed range and depth are always in the name; other hyperparameters
    appear only when they differ from the defaults, so a default run's name
    stays short and a tuned run says what was tuned. A stratified run is
    always marked (`_top-10pct`), and a groups-subset run lists its groups
    (`_groups-mobility-geography`) -- neither may masquerade as a full run.
    """
    name = f"{date.today()}_seeds-{min(seeds)}-{max(seeds)}_max-depth-{params['max_depth']}"
    for key in ("n_estimators", "learning_rate", "num_leaves"):
        if params[key] != DEFAULT_PARAMS[key]:
            name += f"_{key.replace('_', '-')}-{params[key]}"
    if top_percent is not None:
        name += f"_top-{top_percent:g}pct"
    if groups is not None:
        name += "_groups-" + "-".join(groups)
    return config.DATA_DIR / "prediction" / "regression" / name


def _resolve_groups(groups: list[str] | None) -> dict[str, list[str] | None]:
    """Selectors -> {output name: feature list} (None marks the full matrix).

    Default (no flag): the full baseline plus every model group. With
    selectors: exactly those, accepted as letters ("D"), slugs ("mobility"),
    or "full" for the baseline; output names are always slugs, so a letter
    run and a slug run of the same group land in the same CSV vocabulary.
    Unknown selectors raise (in `manifest.group_features`).
    """
    if groups is None:
        selected = [FULL] + list(manifest.GROUP_SLUGS.values())
    else:
        selected = groups
    resolved: dict[str, list[str] | None] = {}
    for sel in selected:
        if sel == FULL:
            resolved[FULL] = None
        else:
            slug = manifest.GROUP_SLUGS.get(sel, sel)
            resolved[slug] = manifest.group_features([sel])
    return resolved


def _filter_top_percent(df: pd.DataFrame, top_percent: float) -> pd.Series:
    """Shrink `keep` to the kept counties in the top X% by Hispanic population.

    The cutoff is computed on the KEPT (complete-case) counties -- computed
    on all rows, incomplete counties would distort the percentile. The mask
    is built on the FULL frame so its index matches `keep`.
    """
    hisp = df.loc[keep, WEIGHT_COL]
    cutoff = hisp.quantile(1 - top_percent / 100)
    big_enough = df[WEIGHT_COL] >= cutoff
    keep = big_enough & keep
    print(
        f"top {top_percent:g}% by Hispanic population: "
        f"cutoff {cutoff:,.0f} -> {int(keep.sum()):,} counties"
    )
    return keep


def run_group_stability(
    seeds: list[int],
    params: dict | None = None,
    top_percent: float | None = None,
    groups: list[str] | None = None,
) -> pd.DataFrame:
    params = {**DEFAULT_PARAMS, **(params or {})}
    selected = _resolve_groups(groups)
    df = pd.read_parquet(config.DATA_DIR / "national_counties" / "processed.parquet")
    out_dir = _run_dir(
        seeds, params, top_percent, groups=None if groups is None else list(selected)
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # One sample for everything: complete-case on the full matrix AND targets.
    X = feature_frame(df)
    keep = pd.concat([X, df[TARGETS]], axis=1).notna().all(axis=1)
    if top_percent is not None:
        keep = _filter_top_percent(df, top_percent)
    X = X.loc[keep]
    weightings = {
        "unweighted": None,
        "weighted": df.loc[keep, WEIGHT_COL],
    }

    # Every selected matrix is a slice of the SAME rows (None = full matrix).
    matrices = {name: X if cols is None else X[cols] for name, cols in selected.items()}

    n_fits = (
        len(seeds) * len(matrices) * len(MODEL_LABELS) * len(weightings) * len(TARGETS)
    )
    print(
        f"group stability -> {out_dir}\n"
        f"{len(X):,} counties (complete on the full matrix) · "
        f"matrices: {', '.join(matrices)} · "
        f"params {params} · {len(seeds)} seeds -> {n_fits} fits"
    )

    rows = []
    started = time.time()
    for i, seed in enumerate(seeds, start=1):
        for group_name, X_g in matrices.items():
            for model in MODEL_LABELS:
                for wname, w in weightings.items():
                    for target in TARGETS:
                        metrics = fit_one(
                            X_g,
                            df.loc[keep, target],
                            model,
                            seed,
                            weights=w,
                            params=params,
                        )
                        rows.append(
                            {
                                "group": group_name,
                                "target": target,
                                "n_features": X_g.shape[1],
                                **metrics,
                            }
                        )
        elapsed = time.time() - started
        print(
            f"  seed {seed} ({i}/{len(seeds)}) · {elapsed:5.0f}s elapsed · "
            f"~{elapsed / i * (len(seeds) - i):4.0f}s remaining"
        )

    by_seed = pd.DataFrame(rows)
    summary = (
        by_seed.groupby(["group", "model", "weighting", "target"])
        .agg(
            n_features=("n_features", "first"),
            mean_r2=("r2", "mean"),
            sd_r2=("r2", "std"),
            min_r2=("r2", "min"),
            max_r2=("r2", "max"),
            mean_rmse=("rmse", "mean"),
            mean_ess=("ess", "mean"),
            min_ess=("ess", "min"),
            max_ess=("ess", "max"),
        )
        .reset_index()
    )

    by_seed.to_csv(out_dir / "group_metrics_by_seed.csv", index=False)
    summary.to_csv(out_dir / "group_summary.csv", index=False)
    figures.plot_group_comparison(summary, out_dir, n_seeds=len(seeds))
    print(f"wrote group-stability outputs -> {out_dir}")
    return summary


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Group-stability regression sweep (three peer models)."
    )
    parser.add_argument(
        "--seeds",
        nargs=2,
        type=int,
        default=[1, 50],
        metavar=("LO", "HI"),
        help="inclusive seed range (default: 1 50)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=DEFAULT_PARAMS["max_depth"],
        help="tree depth cap for rf and lgbm",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=DEFAULT_PARAMS["n_estimators"],
        help="number of trees for rf and lgbm",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=DEFAULT_PARAMS["learning_rate"],
        help="lgbm learning rate",
    )
    parser.add_argument(
        "--num-leaves",
        type=int,
        default=DEFAULT_PARAMS["num_leaves"],
        help="lgbm leaf cap",
    )
    parser.add_argument(
        "--top-percent",
        type=float,
        default=None,
        metavar="X",
        help="restrict to the counties in the top X%% by Hispanic population "
        "(cutoff computed after complete-case filtering)",
    )
    parser.add_argument(
        "--groups",
        nargs="+",
        default=None,
        metavar="G",
        help="run only these matrices: group letters (D J), slugs (mobility "
        "geography), and/or 'full' for the baseline; default runs full + all "
        "groups. Rows stay complete-case on the FULL matrix either way, so "
        "subset runs remain comparable to full runs.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    lo, hi = args.seeds
    run_group_stability(
        seeds=list(range(lo, hi + 1)),
        params={
            "max_depth": args.max_depth,
            "n_estimators": args.n_estimators,
            "learning_rate": args.learning_rate,
            "num_leaves": args.num_leaves,
        },
        top_percent=args.top_percent,
        groups=args.groups,
    )
