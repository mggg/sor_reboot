"""Driver: per-state tract-level analysis (was `statetractcleanedjune.ipynb`).

Same descriptive pipeline as `run_national` (ingest -> merge -> race features ->
scatter/correlations -> spatial), but at census-tract resolution and run once per
state (CA / TX / FL / NY). It reuses the shared ingest/clean/analysis modules; only
the geography level, per-state data sources, and clustering thresholds differ.

Outputs are namespaced per state under data/tract/<STATE>/ (dataset.parquet, plus
scatter/ and spatial/ sections). Each step is checkpointed via `confirm_rerun`.

Run with:  python -m sor_pipeline.run_tract            # all states
           python -m sor_pipeline.run_tract --state CA  # just one
"""

from __future__ import annotations

import argparse

import pandas as pd
import matplotlib

matplotlib.use("Agg")  # headless: figures save to files instead of opening a window

from sor_pipeline.utils import config
from sor_pipeline.utils.checkpoint import confirm_rerun
from sor_pipeline.ingest import census_api, geometry, election, store
from sor_pipeline.clean import merge, features
from sor_pipeline.analysis import viz, correlations, report, spatial

# Same analysis specs as the national spatial runner (the tract notebook is its twin).
from sor_pipeline.runners.national.run_spatial_analysis import (
    RATE_COLUMNS,
    HALF_EDGE_PAIRS,
    EB_SPECS,
)


def _build_tract_dataset(state: str, fips: str) -> pd.DataFrame:
    """Ingest + merge + race features for one state's tracts."""
    for_geo, in_geo = "tract:*", f"state:{fips}"
    pl_total, pl_hispanic = census_api.fetch_decennial_pl(for_geo, in_geo)
    acs = census_api.fetch_acs(for_geo, in_geo)
    geo = geometry.load_tract_geometry(fips)
    elec = election.load_tract_election(state)

    df = merge.merge_sources(pl_total, pl_hispanic, acs, geo, elec, level="tract")
    df = features.add_race_percentages(df)
    df = features.add_ratios(df)
    df = features.add_dominant_race_choice(df)
    df = features.add_hispanic_race_counts(df)
    return df


def process_state(state: str, fips: str) -> None:
    """Run the full descriptive pipeline for one state's tracts."""
    print(f"\n########## {state} (FIPS {fips}) ##########")
    state_dir = config.TRACT_DIR / state
    scatter_dir = state_dir / "scatter"
    scatter_cov = scatter_dir / "by_covariate"
    spatial_dir = state_dir / "spatial"
    parquet = state_dir / "dataset.parquet"
    corr_csv = scatter_dir / "correlations.csv"
    dual_graph = spatial_dir / "dual_graph.json"

    # --- Step 1: build the tract dataset ---
    if confirm_rerun(parquet, f"{state} build dataset"):
        df = _build_tract_dataset(state, fips)
        store.save(df, parquet)
        print(f"  wrote {len(df):,} tracts -> {parquet}")
    else:
        df = store.load(parquet)
        print(f"  loaded {len(df):,} tracts from {parquet}")

    # --- Step 2: scatter figures ---
    if confirm_rerun(scatter_dir, f"{state} scatter figures"):
        scatter_cov.mkdir(parents=True, exist_ok=True)
        viz.plot_baseline_scatter(df, save_path=scatter_dir / "baseline.png")
        for variable in config.VARS_LOG:
            viz.plot_three_panel_scatter(
                df, variable, config.Y_VARS, log_color=True,
                save_path=scatter_cov / f"log_{variable}.png",
            )
        for variable in config.VARS_NO_LOG:
            viz.plot_three_panel_scatter(
                df, variable, config.Y_VARS, log_color=False,
                save_path=scatter_cov / f"{variable}.png",
            )
        print(f"  wrote scatter figures -> {scatter_dir}")

    # --- Step 3: Pearson correlations + scatter README ---
    if confirm_rerun(corr_csv, f"{state} correlations"):
        scatter_dir.mkdir(parents=True, exist_ok=True)
        table = correlations.correlation_table(df)
        table.to_csv(corr_csv)
        readme = scatter_dir / "README.md"
        figs = [scatter_dir / "baseline.png"] + sorted(scatter_cov.glob("*.png"))
        body = (
            f"{state} tracts: race-choice share vs. Hispanic share, one panel per race choice.\n\n"
            "## Correlations (Pearson, covariate vs. race-to-Hispanic ratio)\n\n"
            + report.df_to_md(table, index_label="covariate")
            + "\n\n## Figures\n\n"
            + report.embed_figures(figs, readme.parent)
            + "\n\n## Data files\n\n- [`correlations.csv`](correlations.csv)\n"
        )
        report.write_section_readme(readme, f"{state} tract scatter analysis", body)
        print(f"  wrote correlations -> {corr_csv}")

    # --- Step 4: spatial analysis (clustering -> Moran's I, half-edge, dual graph) ---
    if confirm_rerun(spatial_dir, f"{state} spatial analysis"):
        spatial_dir.mkdir(parents=True, exist_ok=True)
        gdf = df.reset_index(drop=True)  # clustering uses positional indices
        gdf["STATEFP"] = gdf["GEOID"].str[:2]

        labels = spatial.cluster_small_population(gdf, config.TRACT_MIN_POP[state])
        clustered = spatial.dissolve_clusters(gdf, labels)
        clustered, w = spatial.build_rook_weights(clustered)
        if w is None:
            print(f"  {state}: no clusters remain after dropping islands; skipping spatial analysis.")
            return

        moran = spatial.morans_i(clustered, w, RATE_COLUMNS)

        # Headline stat for the map subtitle, mirroring the national spatial runner.
        r = moran.get("pct_HSOR")
        stats_note = (
            f"Moran's I (SOR-alone share, small-population clustering method): "
            f"{r['I']:.2f} vs. null of {r['EI']:.2f}, p={r['p_sim']:.3f}"
            if r
            else None
        )

        states_outline = gdf.dissolve(by="STATEFP").to_crs(epsg=3857)
        graph = spatial.build_dual_graph(clustered, dual_graph)
        viz.plot_dual_graph(
            graph,
            save_path=spatial_dir / f"{state}_dual_graph.html",
            region_name=state,
            unit_plural="tracts",
            state_outlines=states_outline,
            stats_note=stats_note,
            min_cluster_pop=config.TRACT_MIN_POP[state],
        )
        half_edge_scores = {
            label: spatial.half_edge(graph, x_col, y_col)
            for label, x_col, y_col in HALF_EDGE_PAIRS
        }

        # Raw + Empirical-Bayes Moran's I on the raw tracts (HISPANIC > 0).
        gdf_eb = gdf[gdf["HISPANIC"] > 0].copy()
        gdf_eb["dem_base"] = gdf_eb["E_20_PRES_DEM"] + gdf_eb["E_20_PRES_REP"] + 1
        raw = {label: spatial.raw_moran(gdf_eb, c, b) for label, c, b in EB_SPECS}
        eb = {label: spatial.empirical_bayes_moran(gdf_eb, c, b) for label, c, b in EB_SPECS}

        # Section README mirroring the national spatial section.
        moran_df = pd.DataFrame(moran).T[["I", "EI", "p_sim"]]
        raw_df = pd.DataFrame(raw).T[["I", "EI", "p_sim"]]
        eb_df = pd.DataFrame(eb).T[["I", "EI", "p_sim"]]
        he_df = pd.DataFrame({"half_edge_score": half_edge_scores})

        # Co-located data files: the spatial stats as CSVs next to the README.
        moran_csv = pd.concat(
            [
                raw_df.rename_axis("key").reset_index().assign(method="raw"),
                moran_df.rename_axis("key").reset_index().assign(method="clustered"),
                eb_df.rename_axis("key").reset_index().assign(method="empirical_bayes"),
            ],
            ignore_index=True,
        )[["method", "key", "I", "EI", "p_sim"]]
        moran_csv.to_csv(spatial_dir / "moran.csv", index=False)
        he_df.to_csv(spatial_dir / "half_edge.csv")

        readme = spatial_dir / "README.md"
        body = (
            f"{state} tracts: is Hispanic race choice spatially clustered? Clustering "
            f"uses a state-specific minimum Hispanic population "
            f"(MIN_POP={config.TRACT_MIN_POP[state]}).\n\n"
            "## Dual graph\n\n"
            + report.embed_figures([spatial_dir / f"{state}_dual_graph.html"], readme.parent)
            + "\n\n## Moran's I — raw baseline (no denoising)\n\n"
            + report.df_to_md(raw_df, index_label="rate")
            + "\n\n## Moran's I — clustered\n\n"
            + report.df_to_md(moran_df, index_label="rate")
            + "\n\n## Moran's I — Empirical Bayes\n\n"
            + report.df_to_md(eb_df, index_label="rate")
            + "\n\n## CAPY half-edge scores\n\n"
            + report.df_to_md(he_df, index_label="group")
            + "\n\n## Data files\n\n"
            "- [`moran.csv`](moran.csv)\n"
            "- [`half_edge.csv`](half_edge.csv)\n"
        )
        report.write_section_readme(readme, f"{state} tract spatial analysis", body)
        print(f"  wrote dual graph -> {dual_graph}")
        print(f"  wrote spatial figures + summary -> {spatial_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tract-level SOR analysis (all states, or one).")
    parser.add_argument(
        "--state", choices=sorted(config.STATE_FIPS), default=None,
        help="Run a single state; omit to run all available states.",
    )
    args = parser.parse_args()

    config.TRACT_DIR.mkdir(parents=True, exist_ok=True)
    states = [args.state] if args.state else list(config.STATE_FIPS)
    for state in states:
        process_state(state, config.STATE_FIPS[state])


if __name__ == "__main__":
    main()
