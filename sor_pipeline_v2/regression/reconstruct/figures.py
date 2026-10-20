"""The two reconstruction figures.

Figure 1 asks how much of the column is recoverable and how many features
it takes; figure 2 asks whether each of those features is useful on its own
or only alongside the others. They were one combined chart until the two
questions made it unreadable.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_curve(curve: pd.DataFrame, summary: dict, output_path: Path) -> Path:
    """Figure 1: what each chosen feature adds, in selection order.

    One series, one question: how much of the column is recoverable and
    how many features it takes.
    """
    figure, axes = plt.subplots(figsize=(8, 0.55 * len(curve) + 2.6))
    positions = np.arange(len(curve))
    axes.barh(positions, curve.marginal_gain, color="#2a78d6", height=0.6)
    axes.set_yticks(positions)
    axes.set_yticklabels(curve.feature, fontsize=9)
    axes.invert_yaxis()

    span = curve.marginal_gain.max()
    for position, gain, cumulative in zip(
        positions, curve.marginal_gain, curve.cumulative_r2
    ):
        axes.text(
            gain + span * 0.03,
            # float(): np.arange yields np.int_, which the stubs reject here.
            float(position),
            f"{cumulative:.0%} explained so far",
            va="center",
            fontsize=8,
            color="0.35",
        )
    axes.set_xlim(0, span * 1.5)
    axes.set_xlabel(
        f"extra share of {summary['feature']}'s county-to-county variation\n"
        "explained by adding this feature"
    )
    axes.set_title(
        f"How much of {summary['feature']} is already contained in the other features?\n"
        f"{summary['sample']} · all {summary['n_other_features']} features together "
        f"explain {summary['r2_ceiling']:.0%}",
        fontsize=10,
    )
    axes.spines[["top", "right"]].set_visible(False)
    figure.text(
        0.5,
        -0.01,
        "Features are added one at a time, each chosen because it explains the most that "
        "the ones above it do not.\nA short bar means the features above it already carry "
        "that information. Percentages are R\u00b2: 100% would mean\nthe other features "
        "reproduce this one exactly, 0% that they say nothing about it.",
        ha="center",
        va="top",
        fontsize=8,
        color="0.35",
    )
    figure.tight_layout()
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return output_path


def plot_solo_versus_added(
    curve: pd.DataFrame, summary: dict, output_path: Path
) -> Path:
    """Figure 2: is each feature useful alone, or only in combination?

    Above the diagonal a feature contributes MORE here than it could on its
    own -- it complements what came before. Below it, the feature is
    informative by itself but largely redundant once the others are in.
    """
    figure, axes = plt.subplots(figsize=(7, 5.6))
    limit_low = min(0.0, curve.solo_r2.min()) - 0.03
    limit_high = max(curve.solo_r2.max(), curve.marginal_gain.max()) + 0.08
    axes.plot(
        [limit_low, limit_high],
        [limit_low, limit_high],
        linestyle="--",
        linewidth=1,
        color="0.6",
    )
    axes.axhline(0, color="0.85", linewidth=1)
    axes.axvline(0, color="0.85", linewidth=1)
    axes.scatter(curve.solo_r2, curve.marginal_gain, s=70, color="#2a78d6", zorder=3)
    # zip the columns rather than itertuples: the stubs type a namedtuple
    # field as Scalar (possibly bytes), which annotate will not take.
    for name, solo_r2, gain in zip(curve.feature, curve.solo_r2, curve.marginal_gain):
        axes.annotate(
            str(name),
            (float(solo_r2), float(gain)),
            textcoords="offset points",
            xytext=(8, 5),
            fontsize=8,
        )
    axes.set_xlim(limit_low, limit_high)
    axes.set_ylim(limit_low, limit_high)
    axes.set_xlabel(f"explains on its own (R² predicting {summary['feature']})")
    axes.set_ylabel("adds here, after the features selected before it")
    axes.set_title(
        f"Useful alone, or only in combination?  {summary['feature']}\n"
        f"{summary['sample']}",
        fontsize=10,
    )
    axes.spines[["top", "right"]].set_visible(False)
    figure.text(
        0.5,
        -0.01,
        "Dashed line: a feature contributing exactly what it is worth alone. Above it, the "
        "feature only becomes\nuseful alongside the others (a complement). Below it, the "
        "feature is informative by itself but the\nfeatures already chosen carry that same "
        "information.",
        ha="center",
        va="top",
        fontsize=8,
        color="0.35",
    )
    figure.tight_layout()
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return output_path
