"""Rendering for SHAP figures: the beeswarm and per-county waterfalls."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # file output only
import matplotlib.colors
import matplotlib.pyplot as plt
import shap
from matplotlib import patheffects
from matplotlib.axes import Axes

from feature_report.column_meanings import column_meanings, meaning_for
from utils import config

# Longer than this and the labels crowd out the plot itself; the longest
# declared display name runs 64 characters.
MAX_LABEL_CHARS = 46


def feature_display_names(columns: Sequence[str]) -> list[str]:
    """Column names -> the display names the declarations already carry.

    A SHAP figure is the one output a reader meets a feature in without
    the codebook beside them, and HISPFBOTHERLTVW tells them nothing. The
    declarations have written a display name for every variable; this is
    only the lookup, so a renamed or reworded variable reaches the figures
    without anything here changing.

    Parameters
    ----------
    columns : sequence of str
        The feature matrix's column names, in order.

    Returns
    -------
    list of str
        One label per column, truncated to MAX_LABEL_CHARS. A column with
        no declaration keeps its own name, so an undeclared column is
        visible rather than blank.
    """
    meanings = column_meanings()
    labels = []
    for column in columns:
        label = meaning_for(column, meanings).display_name
        if len(label) > MAX_LABEL_CHARS:
            label = label[: MAX_LABEL_CHARS - 1].rstrip() + "\u2026"
        labels.append(label)
    return labels


def plot_beeswarm(explanation, title: str, output_path: Path) -> None:
    plt.figure()
    shap.plots.beeswarm(explanation, max_display=15, show=False)
    plt.title(title, fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=config.FIGURE_DPI, bbox_inches="tight")
    plt.close("all")


def plot_waterfall(
    county_explanation,
    county_title: str,
    actual: float,
    predicted: float,
    target_label: str,
    model_note: str,
    sample_note: str,
    output_path: Path,
    unit_noun: str = "county",
) -> None:
    plt.figure()
    shap.plots.waterfall(county_explanation, max_display=12, show=False)
    _outline_white_bar_labels(plt.gca())
    plt.title(
        f"{county_title} — {target_label}\n"
        f"actual {actual:.1%} of Hispanic residents · "
        f"the model predicts {predicted:.1%}\n"
        f"{model_note} — {sample_note}",
        fontsize=10,
    )
    plt.figtext(
        0.5,
        -0.02,
        f"gray number = this {unit_noun}'s value of that feature · each bar = "
        "the feature's push on the prediction (red up, blue down)\n"
        "E[f(X)] = the model's average prediction over this sample (the "
        f"baseline) · f(x) = its prediction for this {unit_noun}",
        ha="center",
        va="top",
        fontsize=8,
        color="0.35",
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=config.FIGURE_DPI, bbox_inches="tight")
    plt.close("all")
    print(f"  {county_title}: waterfall written")


def _outline_white_bar_labels(ax: Axes) -> None:
    """shap prints bar values in white, which vanishes where a label overflows
    a short bar onto the background; it offers no styling hook, so outline."""
    for text in ax.texts:
        if matplotlib.colors.to_hex(text.get_color()) == "#ffffff":
            text.set_path_effects(
                [patheffects.withStroke(linewidth=1.5, foreground="0.45")]
            )
