"""One histogram per feature, plus a feature grid of the whole group.

Each panel carries the numbers you need to read the shape honestly: the
median and mean as lines (they separate when a feature is skewed), the
analysed row count, and the share of rows sitting at exactly zero, which
is the dominant shape in Hispanic-subpopulation shares and is invisible
in a mean.

Standalone re-render is deliberately not offered: a figure here is one
cheap pass over a parquet, so regenerating means rerunning the report.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # file output only; never requires a display

from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter, MaxNLocator

from feature_report.metadata import ColumnMeaning, meaning_for

# 150 leaves a histogram at 900x540, which is soft on any current
# display and softer still in the feature grid, where that budget is
# split across panels. matplotlib draws from vector internally, so this
# is purely a question of what we ask it to raster at.
DEFAULT_DPI = 200
# Vector formats ignore DPI entirely and stay sharp at any zoom, which is
# what a figure pasted into a memo or a slide actually wants.
VECTOR_FORMATS = ("pdf", "svg")

# Fixed rather than inferred. An automatic rule (Freedman-Diaconis) picks
# its width from the spread of the bulk, which these features do not
# have: a spike at zero holding half the rows plus a long thin tail makes
# it choose either two bins or two thousand.
HISTOGRAM_BINS = 50
# The feature grid's width in panels; four across stays legible at the
# page widths these get pasted into.
GRID_COLUMNS = 4
# Per-panel inches on the feature grid. Bigger than it looks necessary:
# a panel rasters at this size times the DPI, and the sheet is the figure
# people zoom into.
GRID_PANEL_SIZE = (5.0, 3.2)
# Above this, tick labels are abbreviated: a dollar feature running to
# 300,000 otherwise prints six ticks that collide into one smear.
ABBREVIATE_ABOVE = 10_000
# Few enough that abbreviated labels never touch.
MAX_X_TICKS = 6
# Titles wrap rather than run off the canvas; a feature name plus the
# formula is routinely wider than the figure. Measured, not guessed:
# 110 characters of 8pt Helvetica Neue occupy 5.3 of the 6.95 inches a
# left-aligned title has here, and it puts 122 of the 126 descriptions
# on one line. The four it does not are 179 to 281 characters long --
# paragraphs rather than labels, which no width would fit.
TITLE_WIDTH = 110
# Wide enough that the scope line, which is deliberately never wrapped,
# fits on one line at TITLE_FONT_SIZE.
FIGURE_SIZE = (8.0, 5.0)
# Nothing here truncates. metadata.py budgets each side of a formula by
# length and counts whatever does not fit ("+ 12 more"), so the longest
# line any column produces is 106 characters, which this width holds at
# TITLE_FONT_SIZE with room to spare.
HEADLINE_FONT_SIZE = 11
TITLE_FONT_SIZE = 8
MEDIAN_COLOR = "#3b7a57"
MEAN_COLOR = "#b24745"
BAR_COLOR = "#8ba0b6"


def write_distributions(
    sample_df: pd.DataFrame,
    output_dir: Path,
    geographic_unit: Literal["counties", "tracts"],
    scope_note: str,
    scope_phrase: str,
    meanings: dict[str, ColumnMeaning],
    dpi: int = DEFAULT_DPI,
    image_format: str = "png",
) -> list[Path]:
    """Write one `hist_<FEATURE>.png` per column, plus one feature grid.

    Parameters
    ----------
    sample_df : pandas.DataFrame
        The analysed values; one panel per column, in the order given.
    output_dir : Path
        Directory to write into; created if absent.
    geographic_unit : Literal["counties", "tracts"]
        What a row is ("counties", "tracts"), for the y-axis label.
    scope_note : str
        One line naming the geography and the sample, printed under
        every title so a figure read on its own still says what it
        covers. Never wrapped -- it reads as one line or not at all.
    scope_phrase : str
        The short form for the centred headline, e.g. "the California
        tract level".
    meanings : dict
        Column name -> its meaning, from `metadata.column_meanings`.
    dpi : int
        Raster resolution. Ignored by the vector formats.
    image_format : str
        "png", "pdf" or "svg"; the vector two stay sharp at any zoom.

    Returns
    -------
    list of Path
        Every file written, the feature grid last.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    _use_report_fonts()

    figure_paths: list[Path] = []
    for column_name in sample_df.columns:
        column_values = sample_df[column_name]
        meaning = meaning_for(str(column_name), meanings)
        figure, axes = plt.subplots(figsize=FIGURE_SIZE)
        _draw_histogram(axes, column_values, meaning, geographic_unit)
        # Two text objects, not one: set_title applies a single
        # alignment to its whole string, so a centred headline above a
        # left-aligned block has to be drawn separately.
        figure.suptitle(_headline(meaning, scope_phrase), fontsize=HEADLINE_FONT_SIZE)
        axes.set_title(
            _title_block(meaning, scope_note), fontsize=TITLE_FONT_SIZE, loc="left"
        )
        figure.tight_layout()
        path = output_dir / f"hist_{column_name}.{image_format}"
        figure.savefig(path, dpi=dpi)
        plt.close(figure)
        figure_paths.append(path)

    figure_paths.append(
        _write_feature_grid(
            sample_df,
            output_dir,
            geographic_unit,
            scope_note,
            meanings,
            dpi,
            image_format,
        )
    )
    return figure_paths


def _headline(meaning: ColumnMeaning, scope_phrase: str) -> str:
    """The centred top line: what is plotted, and over what geography."""
    return f"{meaning.display_name} at {scope_phrase}"


def _title_block(meaning: ColumnMeaning, scope_note: str) -> str:
    """The left-aligned block under the headline.

    What the column means, how it was computed, and what rows it covers.
    The formula line is the one that stops a reader guessing whether a
    share is OF everybody or OF the Hispanic population -- the two give
    very different pictures of the same place.

    Only the description wraps. The formula and the scope each occupy
    exactly one line, both by being short enough already -- nothing is
    cut, so no line trails off without saying what it dropped.
    """
    lines = [f"({meaning.column})"]
    if meaning.description:
        lines.append(textwrap.fill(meaning.description, TITLE_WIDTH))
    if meaning.formula:
        # Neither wrapped nor cut: metadata.py has already made it short
        # enough, by counting the terms it does not name.
        lines.append(f"Calculated as: {meaning.formula}")
    # Deliberately unwrapped: the scope reads as one line or not at all,
    # which is what FIGURE_SIZE is sized for.
    lines.append(scope_note)
    return "\n".join(lines)


def _x_axis_label(meaning: ColumnMeaning) -> str:
    """What one number on the x axis IS -- a share of what, or a level."""
    if meaning.universe:
        return f"{meaning.display_name}\n(share of {meaning.universe})"
    return meaning.display_name


def _draw_histogram(
    axes: Axes, values: pd.Series, meaning: ColumnMeaning, geographic_unit: str
) -> None:
    """One histogram with its median, mean and zero-share annotation."""
    non_null_values = values.dropna().to_numpy(dtype=float)
    if not non_null_values.size:
        axes.text(0.5, 0.5, "no values", ha="center", transform=axes.transAxes)
        return

    axes.hist(non_null_values, bins=HISTOGRAM_BINS, color=BAR_COLOR, edgecolor="white")
    median, mean = float(np.median(non_null_values)), float(non_null_values.mean())
    axes.axvline(
        median, color=MEDIAN_COLOR, lw=1.6, label=f"median {_legend_value(median)}"
    )
    axes.axvline(
        mean, color=MEAN_COLOR, lw=1.6, ls="--", label=f"mean {_legend_value(mean)}"
    )
    axes.set_xlabel(_x_axis_label(meaning), fontsize=8)

    axes.set_ylabel(f"number of {geographic_unit}", fontsize=8)
    axes.legend(fontsize=7, frameon=False)
    if float(np.abs(non_null_values).max()) >= ABBREVIATE_ABOVE:
        axes.xaxis.set_major_locator(MaxNLocator(MAX_X_TICKS))
        axes.xaxis.set_major_formatter(FuncFormatter(_abbreviate_tick))

    zero_share = float((non_null_values == 0).mean())
    corner_note = f"n={non_null_values.size:,}"
    if zero_share:
        corner_note += f"   {zero_share:.0%} exactly zero"
    axes.text(
        0.98,
        0.98,
        corner_note,
        transform=axes.transAxes,
        ha="right",
        va="top",
        fontsize=7,
        color="#555555",
    )


def _abbreviate_tick(value: float, _position: int = 0) -> str:
    """A large tick as 25k or 1.2M, so six of them fit on one axis."""
    for scale, suffix in ((1_000_000, "M"), (1_000, "k")):
        if abs(value) >= scale:
            return f"{value / scale:,.3g}{suffix}"
    return f"{value:,.0f}"


def _legend_value(value: float) -> str:
    """A value for the legend, matching the axis rather than fighting it.

    Plain formatting would print 2.312e+04 next to an axis reading 24k.
    """
    return (
        _abbreviate_tick(value) if abs(value) >= ABBREVIATE_ABOVE else f"{value:,.4g}"
    )


def _write_feature_grid(
    sample_df: pd.DataFrame,
    output_dir: Path,
    geographic_unit: Literal["counties", "tracts"],
    scope_note: str,
    meanings: dict[str, ColumnMeaning],
    dpi: int,
    image_format: str,
) -> Path:
    """Every feature on one grid, for scanning the group at a glance."""
    n_panels = len(sample_df.columns)
    n_rows = -(-n_panels // GRID_COLUMNS)  # ceiling division
    panel_width, panel_height = GRID_PANEL_SIZE
    figure, axes_grid = plt.subplots(
        n_rows,
        GRID_COLUMNS,
        figsize=(panel_width * GRID_COLUMNS, panel_height * n_rows),
        squeeze=False,
    )
    panels = axes_grid.ravel()
    for axes, column_name in zip(panels, sample_df.columns, strict=False):
        column_values = sample_df[column_name]
        meaning = meaning_for(str(column_name), meanings)
        _draw_histogram(axes, column_values, meaning, geographic_unit)
        axes.set_title(
            f"{meaning.display_name}  ({meaning.column})", fontsize=8, loc="left"
        )
    for axes in panels[n_panels:]:
        axes.axis("off")

    figure.suptitle(scope_note, fontsize=10, x=0.01, ha="left")
    figure.tight_layout(rect=(0, 0, 1, 0.98))
    path = output_dir / f"distributions.{image_format}"
    figure.savefig(path, dpi=dpi)
    plt.close(figure)
    return path


def _use_report_fonts() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Neue"],
            "mathtext.fontset": "dejavusans",
        }
    )
