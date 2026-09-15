"""The group-comparison figure: R² by feature group, unweighted above weighted.

One figure per target. Stacked panels on one shared x scale, each panel
ranking its own groups by that weighting's best mean R² -- the rank shuffle
between panels (geography, income) is itself a finding. `full` sits on top
of each panel as the baseline every group is read against.

Settled design decisions: Helvetica Neue, shared x axis, per-panel ranking,
one fixed hue per model, and the caption warning that the two panels score
different questions (places vs people).

Standalone re-render (no re-fitting):
`python -m regression.figures <run_dir>` reads `group_summary.csv` there
and rewrites the PNGs beside it.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # file output only; never requires a display
import matplotlib.pyplot as plt
import pandas as pd

FULL = "full"

# One fixed hue per estimator, so a figure's color says which model it
# describes everywhere in the pipeline.
MODEL_COLORS = {
    "random_forest": "#b24745",
    "lightgbm": "#d9822b",
    "ridge": "#3b7a57",
}


def plot_group_comparison(summary: pd.DataFrame, out_dir, n_seeds: int) -> None:
    """Write `group_comparison_<target>.png` for every target in `summary`."""
    out_dir = Path(out_dir)
    # Helvetica Neue with the closest available math font for the caption's
    # formula.
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Neue"],
            "mathtext.fontset": "dejavusans",
        }
    )
    dodge = {"ridge": -0.22, "random_forest": 0.0, "lightgbm": 0.22}
    # A groups-subset run may carry no `full` baseline; the caption and the
    # pinned top rank then simply go without it.
    full_rows = summary.loc[summary["group"] == FULL, "n_features"]
    full_note = f"full = all {int(full_rows.iloc[0])} features\n" if len(full_rows) else ""
    for target in summary["target"].unique():
        sub = summary[summary["target"] == target]
        n_groups = sub["group"].nunique()
        fig, axes = plt.subplots(2, 1, figsize=(8.5, 0.6 * n_groups + 2.4), sharex=True)
        panels = [
            ("unweighted", "unweighted"),
            ("weighted", "weighted (by Hispanic population)"),
        ]
        for ax, (wkey, wtitle) in zip(axes, panels):
            best = (
                sub[sub["weighting"] == wkey]
                .groupby("group")["mean_r2"]
                .max()
                .sort_values(ascending=False)
            )
            # Each panel ranked by its own weighting's best mean R²; the full
            # baseline (when run) pinned on top.
            order = [FULL] if FULL in best.index else []
            order += [g for g in best.index if g != FULL]
            for model, off in dodge.items():
                rows = sub[
                    (sub["weighting"] == wkey) & (sub["model"] == model)
                ].set_index("group")
                ys = [order.index(g) + off for g in order if g in rows.index]
                vals = [rows.loc[g, "mean_r2"] for g in order if g in rows.index]
                sds = [rows.loc[g, "sd_r2"] for g in order if g in rows.index]
                ax.errorbar(
                    vals, ys, xerr=sds,
                    fmt="o", ms=5.5, ls="none",
                    color=MODEL_COLORS[model], ecolor="0.6",
                    elinewidth=1, capsize=2, label=model, zorder=3,
                )
            if order and order[0] == FULL:
                ax.axhline(0.5, color="0.8", lw=1)  # separate `full` from the groups
            ax.set_title(wtitle, fontsize=10)
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(axis="x", alpha=0.3)
            ax.set_axisbelow(True)
            ax.set_yticks(range(len(order)), order)
            ax.invert_yaxis()
        axes[-1].set_xlabel("mean test R²")
        # Legend above the panels: every in-panel corner can collide with a
        # dot row, since rows span the full height of both panels.
        handles, labels = axes[1].get_legend_handles_labels()
        fig.legend(
            handles, labels, loc="upper center", ncol=3, frameon=False,
            fontsize=8, bbox_to_anchor=(0.5, 1.005),
        )
        fig.suptitle(f"R² by feature group — {target}", fontsize=11, y=1.03)
        fig.text(
            0.5, -0.01,
            f"each dot = mean test R² across the {n_seeds} splits, bar = ±1 sd\n"
            f"{full_note}"
            "the two panels score different questions (places vs people), so their "
            "R² values are measured against different baselines and compare only loosely\n"
            "$R^2 = 1 - SS_{res}/SS_{tot}$, computed on held-out counties, so it can be negative:\n"
            "below 0 means the model predicts the test counties worse than guessing their mean "
            "(1.0 = perfect prediction)",
            ha="center", va="top", fontsize=8, color="0.35",
        )
        fig.tight_layout()
        fig.savefig(
            out_dir / f"group_comparison_{target.replace(' ', '_')}.png",
            dpi=150, bbox_inches="tight",
        )
        plt.close(fig)


if __name__ == "__main__":
    import sys

    run_dir = Path(sys.argv[1])
    summary = pd.read_csv(run_dir / "group_summary.csv")
    # Seed count is not stored in the summary; recover it from the by-seed table.
    by_seed = pd.read_csv(run_dir / "group_metrics_by_seed.csv")
    plot_group_comparison(summary, run_dir, n_seeds=by_seed["seed"].nunique())
    print(f"rewrote figures in {run_dir}")
