"""R²-by-feature-group figures: one per (target, weighting), paired on a shared x scale.

Standalone re-render (no re-fitting): `python -m regression.viz.group_model_comparisons <run_dir>`.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # file output only; never requires a display
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes

from regression.run_config import FULL

# One fixed hue per estimator, everywhere in the pipeline.
MODEL_COLORS = {
    "random_forest": "#b24745",
    "lightgbm": "#d9822b",
    "ridge": "#3b7a57",
}
# Vertical offset per model, so three dots share a group row without overlap.
MODEL_DODGE = {"ridge": -0.22, "random_forest": 0.0, "lightgbm": 0.22}

WEIGHTING_TITLES = {
    "unweighted": "unweighted",
    "weighted": "weighted (by Hispanic population)",
}


def plot_group_comparison(
    summary: pd.DataFrame, output_dir, n_seeds: int, sample_note: str = ""
) -> None:
    """Write `group_comparison_<target>_<weighting>.png` for every target."""
    output_dir = Path(output_dir)
    _use_report_fonts()
    for target in summary["target"].unique():
        target_summary = summary[summary["target"] == target]
        x_limits = _shared_r2_limits(target_summary)
        for weighting in WEIGHTING_TITLES:
            weighting_summary = target_summary[target_summary["weighting"] == weighting]
            if weighting_summary.empty:
                continue
            _plot_one_figure(
                weighting_summary,
                target=target,
                weighting=weighting,
                x_limits=x_limits,
                n_seeds=n_seeds,
                sample_note=sample_note,
                output_dir=output_dir,
            )


def _use_report_fonts() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Neue"],
            "mathtext.fontset": "dejavusans",
        }
    )


def _shared_r2_limits(target_summary: pd.DataFrame) -> tuple[float, float]:
    """One x scale across a target's weighted and unweighted figures.

    A single-seed run has no sd (std of one value is NaN): no bars, so the
    scale is the dots alone.
    """
    sd = target_summary["sd_r2"].fillna(0)
    low = (target_summary["mean_r2"] - sd).min()
    high = (target_summary["mean_r2"] + sd).max()
    padding = 0.04 * ((high - low) or 1.0)
    return low - padding, high + padding


def _group_order(weighting_summary: pd.DataFrame) -> list[str]:
    """Groups ranked by best mean R²; the full baseline (when run) pinned on top."""
    ranked = (
        weighting_summary.groupby("group")["mean_r2"].max().sort_values(ascending=False)
    )
    order = [FULL] if FULL in ranked.index else []
    return order + [group for group in ranked.index if group != FULL]


def _draw_model_dots(
    ax: Axes, weighting_summary: pd.DataFrame, group_order: list[str]
) -> None:
    """One dot ± sd bar per (group, model), dodged so models share a row."""
    for model, offset in MODEL_DODGE.items():
        model_rows = weighting_summary[weighting_summary["model"] == model].set_index(
            "group"
        )
        plotted = [g for g in group_order if g in model_rows.index]
        ax.errorbar(
            [model_rows.loc[g, "mean_r2"] for g in plotted],
            [group_order.index(g) + offset for g in plotted],
            xerr=[model_rows.loc[g, "sd_r2"] for g in plotted],
            fmt="o",
            ms=5.5,
            ls="none",
            color=MODEL_COLORS[model],
            ecolor="0.6",
            elinewidth=1,
            capsize=2,
            label=model,
            zorder=3,
        )


def _caption(n_seeds: int, full_note: str, paired_weighting: str) -> str:
    return (
        f"each dot = mean test R² across the {n_seeds} splits, bar = ±1 sd\n"
        f"{full_note}"
        f"x scale shared with the {paired_weighting} figure; the two weightings "
        "score different questions (places vs people), so compare only loosely\n"
        "$R^2 = 1 - SS_{res}/SS_{tot}$, computed on held-out counties, so it can "
        "be negative:\n"
        "below 0 means the model predicts the test counties worse than guessing "
        "their mean (1.0 = perfect prediction)"
    )


def _plot_one_figure(
    weighting_summary: pd.DataFrame,
    target: str,
    weighting: str,
    x_limits: tuple[float, float],
    n_seeds: int,
    sample_note: str,
    output_dir: Path,
) -> None:
    group_order = _group_order(weighting_summary)
    fig, axes = plt.subplots(figsize=(8.5, 0.6 * len(group_order) + 1.8))

    _draw_model_dots(axes, weighting_summary, group_order)
    if group_order and group_order[0] == FULL:
        axes.axhline(0.5, color="0.8", lw=1)  # separate `full` from the groups
    axes.set_xlim(*x_limits)
    axes.spines[["top", "right"]].set_visible(False)
    axes.grid(axis="x", alpha=0.3)
    axes.set_axisbelow(True)
    axes.set_yticks(range(len(group_order)), group_order)
    axes.invert_yaxis()
    axes.set_xlabel("mean test R²")

    # Legend above the axes: any in-axes corner can collide with a dot row.
    handles, labels = axes.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=3,
        frameon=False,
        fontsize=8,
        bbox_to_anchor=(0.5, 1.0),
    )
    subtitle = WEIGHTING_TITLES[weighting]
    if sample_note:
        subtitle += f" · {sample_note}"
    fig.suptitle(f"R² by feature group — {target}\n{subtitle}", fontsize=11, y=1.1)

    full_rows = weighting_summary.loc[weighting_summary["group"] == FULL, "n_features"]
    full_note = (
        f"full = all {int(full_rows.iloc[0])} features\n" if len(full_rows) else ""
    )
    paired_weighting = "weighted" if weighting == "unweighted" else "unweighted"
    fig.text(
        0.5,
        -0.01,
        _caption(n_seeds, full_note, paired_weighting),
        ha="center",
        va="top",
        fontsize=8,
        color="0.35",
    )

    fig.tight_layout()
    fig.savefig(
        output_dir / f"group_comparison_{target}_{weighting}.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)


if __name__ == "__main__":
    import re
    import sys

    run_dir = Path(sys.argv[1])
    summary = pd.read_csv(run_dir / "group_summary.csv")
    by_seed = pd.read_csv(run_dir / "group_metrics_by_seed.csv")
    stratum = re.search(r"_(top|bottom)-([0-9.]+)pct", run_dir.name)
    sample_note = (
        f"{stratum.group(1)} {stratum.group(2)}% of counties by Hispanic population"
        if stratum
        else "all complete-case counties"
    )
    plot_group_comparison(
        summary, run_dir, n_seeds=by_seed["seed"].nunique(), sample_note=sample_note
    )
    print(f"rewrote figures in {run_dir}")
