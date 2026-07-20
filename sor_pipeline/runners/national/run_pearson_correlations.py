from __future__ import annotations
from ...utils import config
from ...ingest import census_api, geometry, election, store
from ...clean import merge, features
from ...analysis import viz, correlations, report
import pandas as pd


def run_pearson_correlations(df: pd.DataFrame) -> None:
    """Compute Pearson correlations of the race-to-Hispanic ratios and save the results as a CSV file."""
    config.NATIONAL_SCATTER_DIR.mkdir(parents=True, exist_ok=True)
    table = correlations.correlation_table(df)
    table.to_csv(config.CORRELATIONS_PATH)
    print(table.round(3))
    print(f"  wrote correlations -> {config.CORRELATIONS_PATH}")

    readme = config.NATIONAL_SCATTER_DIR / "README.md"
    figs = [config.NATIONAL_SCATTER_DIR / "baseline.png"] + sorted(
        config.NATIONAL_SCATTER_COVARIATE_DIR.glob("*.png")
    )
    body = (
        "Race-choice share vs. Hispanic share, one panel per race choice.\n\n"
        "## Correlations (Pearson, covariate vs. race-to-Hispanic ratio)\n\n"
        + report.df_to_md(table, index_label="covariate")
        + "\n\n## Figures\n\n"
        + report.embed_figures(figs, readme.parent)
        + "\n\n## Data files\n\n"
        "- [`correlations.csv`](correlations.csv)\n"
    )
    report.write_section_readme(readme, "Scatter analysis", body)
    print(f"  wrote section summary -> {readme}")
