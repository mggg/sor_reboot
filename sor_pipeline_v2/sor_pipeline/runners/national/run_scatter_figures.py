from __future__ import annotations
from ...utils import config
from ...ingest import census_api, geometry, election, store
from ...clean import merge, features
from ...analysis import viz
import pandas as pd


def run_scatter_figures(df: pd.DataFrame) -> None:
    """Generate scatter figures that visualize relationships between variables for the national dataset.
    See config.VARS_LOG and config.VARS_NO_LOG for the covariates to plot, and config.Y_VARS for the outcome variables.
    """
    config.NATIONAL_SCATTER_COVARIATE_DIR.mkdir(parents=True, exist_ok=True)
    viz.plot_baseline_scatter(
        df, save_path=config.NATIONAL_SCATTER_DIR / "baseline.png"
    )
    for variable in config.VARS_LOG:
        viz.plot_three_panel_scatter(
            df,
            variable,
            config.Y_VARS,
            log_color=True,
            save_path=config.NATIONAL_SCATTER_COVARIATE_DIR / f"log_{variable}.png",
        )
    for variable in config.VARS_NO_LOG:
        viz.plot_three_panel_scatter(
            df,
            variable,
            config.Y_VARS,
            log_color=False,
            save_path=config.NATIONAL_SCATTER_COVARIATE_DIR / f"{variable}.png",
        )
    print(f"  wrote scatter figures -> {config.NATIONAL_SCATTER_DIR}")
