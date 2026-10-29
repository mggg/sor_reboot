"""One target's mean R² by feature group, across several finished runs: a heatmap.

Rows are feature groups, columns are runs (e.g. US tracts, then one column
per state). Reads each run's `group_summary.csv`; no re-fitting.

    python -m regression.group_stability.state_heatmap \\
        <national_run_dir> <state_run_dir> ... --output <path>.png

The first run directory is the reference column: rows are sorted by it.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from regression.group_stability.figures import _use_report_fonts
from regression.shared.fit import MODEL_DISPLAY_NAMES, MODEL_LABELS
from regression.shared.run_config import (
    FULL,
    REGRESSION_TARGETS,
    find_run_file,
    scope_from_run_dir,
)
from regression.shared.run_metadata import (
    describe_source_run,
    git_state,
    warn_if_uncommitted,
    write_figure_metadata,
)
from utils import config

R2_CMAP = LinearSegmentedColormap.from_list(
    "r2_blues",
    ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
)
GROUP_LABELS = {FULL: "All features"}


def load_r2_matrix(
    run_dirs: list[Path], model: str, weighting: str, target: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Mean R² per (group, run) for one (model, weighting, target) cell.

    Parameters
    ----------
    run_dirs : list of Path
        Finished group-stability run directories, in column order.
    model, weighting, target : str
        Which slice of each `group_summary.csv` to keep.

    Returns
    -------
    tuple
        The mean R² and the across-seed sd of R² (index = group, columns
        = run labels), and the sample size `n` per run label.
    """
    mean_r2, sd_r2, n = {}, {}, {}
    for run_dir in run_dirs:
        summary = pd.read_csv(find_run_file(run_dir, "group_summary"))
        kept = summary[
            (summary["model"] == model)
            & (summary["weighting"] == weighting)
            & (summary["target"] == target)
        ].set_index("group")
        if kept.empty:
            raise ValueError(f"{run_dir} has no {model}/{weighting}/{target} rows")
        label = _column_label(run_dir)
        mean_r2[label] = kept["mean_r2"]
        sd_r2[label] = kept["sd_r2"]
        n[label] = int(kept["n"].iloc[0])
    return pd.DataFrame(mean_r2), pd.DataFrame(sd_r2), pd.Series(n)


def _column_label(run_dir: Path) -> str:
    """A run's column header, e.g. "US" or "CA", from its directory name."""
    _, state_fips = scope_from_run_dir(run_dir.name)
    if state_fips is None:
        return "US"
    return "+".join(config.STATE_FIPS_TO_USPS[fips] for fips in state_fips)


def _group_label(group: str) -> str:
    """A row label: "All features" for FULL, else e.g. "National origin"."""
    if group in GROUP_LABELS:
        return GROUP_LABELS[group]
    return group.replace("_", " ").capitalize()


def _row_order(r2: pd.DataFrame) -> list[str]:
    """FULL pinned on top, then the groups by R² in the reference (first) column."""
    ranked = r2.iloc[:, 0].drop(FULL, errors="ignore").sort_values(ascending=False)
    return ([FULL] if FULL in r2.index else []) + list(ranked.index)


def plot_heatmap(
    r2: pd.DataFrame,
    n: pd.Series,
    output_path: Path,
    title: str,
    subtitle: str,
    caption: str,
) -> None:
    """Draw the heatmap and save it to `output_path`.

    Parameters
    ----------
    r2 : pd.DataFrame
        From `load_r2_matrix`, rows already in display order.
    n : pd.Series
        Sample size per column, shown under each column header.
    output_path : Path
        Where the PNG goes.
    title, subtitle, caption : str
        Figure title, the method line under it, and the small print under
        the figure.
    """
    _use_report_fonts()
    values = r2.to_numpy()
    vmin = np.floor(np.nanmin(values) * 20) / 20
    vmax = np.ceil(np.nanmax(values) * 20) / 20

    fig, ax = plt.subplots(figsize=(0.9 * len(r2.columns) + 3, 0.45 * len(r2) + 1.8))
    image = ax.imshow(values, cmap=R2_CMAP, vmin=vmin, vmax=vmax, aspect="auto")

    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            if np.isnan(value):
                continue
            ax.text(
                col,
                row,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=9,
                color="white" if value > (vmin + vmax) / 2 else "0.1",
            )

    ax.set_yticks(range(len(r2)), [_group_label(str(g)) for g in r2.index])
    ax.set_xticks(
        range(len(r2.columns)), [f"{c}\nn={n[c]:,}" for c in r2.columns], fontsize=9
    )
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_xticks(np.arange(-0.5, len(r2.columns)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(r2)), minor=True)
    ax.grid(which="minor", color="white", lw=1.5)
    ax.tick_params(which="minor", length=0)
    if r2.index[0] == FULL:
        ax.axhline(0.5, color="white", lw=4)
    ax.axvline(0.5, color="white", lw=4)

    colorbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    colorbar.set_label("mean test R² across seeds")
    for spine in colorbar.ax.spines.values():
        spine.set_visible(False)

    title_text = ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=24)
    ax.annotate(
        subtitle,
        xy=(0, 0),
        xycoords=title_text,
        xytext=(0, -4),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=9.5,
        color="0.3",
    )
    fig.text(0.01, 0.0, caption, ha="left", va="top", fontsize=8, color="0.35")
    fig.tight_layout()
    fig.savefig(output_path, dpi=config.FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m regression.group_stability.state_heatmap",
        description="Heatmap of one target's mean R² by feature group, across runs.",
    )
    parser.add_argument(
        "run_dirs",
        nargs="+",
        type=Path,
        help="finished run directories, in column order; the first is the reference",
    )
    parser.add_argument("--output", type=Path, required=True, help="PNG path to write")
    parser.add_argument("--model", default="lightgbm")
    parser.add_argument("--weighting", default="weighted")
    parser.add_argument("--target", default="Hisp_SOR_Alone_Pct_of_Hisp_Pop")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    git = git_state()
    warn_if_uncommitted(git)
    r2, sd, n = load_r2_matrix(args.run_dirs, args.model, args.weighting, args.target)
    order = _row_order(r2)
    r2, sd = r2.loc[order], sd.loc[order]

    reference = r2.columns[0]
    model_key = {label: key for key, label in MODEL_LABELS.items()}.get(args.model, "")
    model_name: str = MODEL_DISPLAY_NAMES.get(model_key, str(args.model))
    level, _ = scope_from_run_dir(args.run_dirs[0].name)
    unit = "counties" if level == "national_counties" else "tracts"
    n_seeds = pd.read_csv(find_run_file(args.run_dirs[0], "group_metrics_by_seed"))[
        "seed"
    ].nunique()
    weighting_note = (
        "weighted by Hispanic population"
        if args.weighting == "weighted"
        else "unweighted"
    )
    subtitle = (
        f"{weighting_note[0].upper()}{weighting_note[1:]}; each cell = mean test R² across "
        f"{n_seeds} train/test splits; n = complete-case {unit}"
    )
    if len(r2.columns) > 1:
        others = sd.drop(columns=reference).max()

    plot_heatmap(
        r2,
        n,
        args.output,
        title=(
            f"{model_name.capitalize()} on {unit}: R² by feature group, "
            f"{REGRESSION_TARGETS.get(args.target, args.target)}"
        ),
        subtitle=subtitle,
        caption="",
    )
    # Every run supplies its summary; the first also its per-seed file,
    # for the seed count in the subtitle.
    source_runs = [
        describe_source_run(
            run_dir,
            [find_run_file(run_dir, "group_summary")]
            + ([find_run_file(run_dir, "group_metrics_by_seed")] if i == 0 else []),
        )
        for i, run_dir in enumerate(args.run_dirs)
    ]
    metadata_path = write_figure_metadata(
        args.output,
        git,
        settings={
            "model": args.model,
            "weighting": args.weighting,
            "target": args.target,
            "columns": list(r2.columns),
            "rows": list(r2.index),
        },
        source_runs=source_runs,
    )
    print(f"wrote {args.output} and {metadata_path.name}")
