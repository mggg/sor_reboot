"""Interactive scatter of out-of-fold residuals, one trace per run.

Hispanic population (log) against the residual, so both things worth seeing
are on one plot: the spread collapsing as population grows (the target
becoming measurable, not the model improving), and the large counties that
still sit far from zero.

Run: `python -m regression.residual.scatter [--min-hispanic N]`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.express as px

from utils import config

RESIDUAL_ROOT = config.DATA_DIR / "prediction" / "regression"


def load_runs(min_hispanic: int = 0) -> pd.DataFrame:
    """Every residual run under the prediction directory, stacked.

    Parameters
    ----------
    min_hispanic : int
        Drop counties below this Hispanic population (their shares are
        computed over too few people to be meaningful).

    Returns
    -------
    pandas.DataFrame
        The residual rows of every run, plus a `run` column naming each.

    Raises
    ------
    FileNotFoundError
        If no residual runs have been written yet.
    """
    frames = []
    for run_dir in sorted(RESIDUAL_ROOT.glob("residuals_*")):
        for csv_path in run_dir.glob("residuals_*.csv"):
            table = pd.read_csv(csv_path, dtype={"GEOID": str})
            table["run"] = run_dir.name.removeprefix("residuals_")
            frames.append(table)
    if not frames:
        raise FileNotFoundError(f"no residual runs under {RESIDUAL_ROOT}")
    stacked = pd.concat(frames, ignore_index=True)
    return stacked[stacked["HISPANIC"] >= min_hispanic]


def plot_residuals(min_hispanic: int = 0, output_path: Path | None = None) -> Path:
    """Write the interactive scatter.

    Parameters
    ----------
    min_hispanic : int
        Population floor, passed to `load_runs`.
    output_path : Path or None
        Where to write the HTML; defaults to the prediction directory.

    Returns
    -------
    Path
        The HTML file written.
    """
    residuals = load_runs(min_hispanic)
    figure = px.scatter(
        residuals,
        x="HISPANIC",
        y="residual",
        color="run",
        log_x=True,
        hover_name="county",
        hover_data={
            "GEOID": True,
            "actual": ":.3f",
            "predicted": ":.3f",
            "residual": ":.3f",
            "HISPANIC": ":,",
            "run": False,
        },
        opacity=0.55,
        labels={
            "HISPANIC": "Hispanic population",
            "residual": "Residual (actual − predicted)",
        },
        title="Out-of-fold residuals by county",
    )
    figure.add_hline(y=0, line_dash="dash", line_width=1, opacity=0.5)
    figure.update_traces(marker_size=6)

    output_path = output_path or RESIDUAL_ROOT / "residual_plot.html"
    figure.write_html(output_path)
    print(
        f"{len(residuals):,} points, {residuals['run'].nunique()} runs -> {output_path}"
    )
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m regression.residual.scatter",
        description="Interactive residual scatter.",
    )
    parser.add_argument("--min-hispanic", type=int, default=0, metavar="N")
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_residuals(args.min_hispanic, args.output)
