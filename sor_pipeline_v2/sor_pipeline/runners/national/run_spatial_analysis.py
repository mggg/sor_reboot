from __future__ import annotations
from pathlib import Path
from ...utils import config
from ...ingest import census_api, geometry, election, store
from ...clean import merge, features
from ...analysis import viz, report, spatial
import pandas as pd

# Cluster-level rate columns fed to Moran's I (built by spatial.dissolve_clusters).
RATE_COLUMNS = [
    "pct_HSOR",
    "pct_HWhiteSOR",
    "pct_HWHITE",
    "pct_HWHITEACOMBO",
    "pct_HISP",
    "pct_DEM",
]

# Half-edge score pairs: (label, count column, its Hispanic complement).
HALF_EDGE_PAIRS = [
    ("SORA", "HSOR", "H_N_SOR"),
    ("White + SOR", "HWHITESOR", "H_N_WHITESOR"),
    ("WhiteA", "HWHITE", "H_N_WHITE"),
    ("White alone or combo", "HWHITEACOMBO", "H_N_WHITEACOMBO"),
    ("Hispanic", "HISPANIC", "NONHISPANIC"),
    ("Democrat vs Republican", "E_20_PRES_DEM", "E_20_PRES_REP"),
]

# Empirical-Bayes Moran's I specs: (label, count column, denominator column).
EB_SPECS = [
    ("SORA", "HSOR", "HISPANIC"),
    ("White + SOR", "HWHITESOR", "HISPANIC"),
    ("WhiteA", "HWHITE", "HISPANIC"),
    ("WhiteAorCombo", "HWHITEACOMBO", "HISPANIC"),
    ("Hispanic", "HISPANIC", "TOTALPOP"),
    ("Democrat", "E_20_PRES_DEM", "dem_base"),
]


def run_spatial_analysis(
    df: pd.DataFrame, include_regions: list[str] | None = None
) -> None:
    """Run the spatial analysis pipeline.

    This is the second step in the SOR pipeline. It computes the dual graph of the
    county geometry, computes spatial autocorrelations, and saves the results as a JSON
    file.
    """
    for region_name, fips in config.REGIONS.items():
        if include_regions is not None and region_name not in include_regions:
            continue
        print(f"Running spatial analysis for {region_name}...")
        gdf = spatial.select_region(df, fips)
        out_dir = config.NATIONAL_SPATIAL_DIR / region_name
        out_dir.mkdir(parents=True, exist_ok=True)
        _analyze_region(gdf, out_dir, region_name)


def _has_variation(series: pd.Series) -> bool:
    """Check if a series has more than one unique value (prevents dividing by 0 later on)."""
    return series.nunique(dropna=True) > 1


def _analyze_region(gdf: pd.DataFrame, out_dir: Path, region_name: str) -> None:
    """Run the spatial analysis for a single region."""

    out_dir.mkdir(parents=True, exist_ok=True)

    # Strategy A: cluster small-Hispanic tracts, then measure on the clusters.
    gdf = spatial.prepare_contiguous(gdf)
    labels = spatial.cluster_small_population(gdf, config.MIN_CLUSTER_HISPANIC)
    print(gdf.describe(include="all").T)
    clustered = spatial.dissolve_clusters(gdf, labels)

    # Island-free clusters + weights, shared by Moran's I and the dual graph.
    before = len(clustered)
    print(f"Number of clusters before dropping islands: {before}")
    clustered, w = spatial.build_rook_weights(clustered)
    if w is None:
        print(
            "No clusters remain after dropping islands; skipping Moran's I and dual graph."
        )
        return
    print(
        f"Number of clusters after dropping islands: {len(clustered)}; dropped {before - len(clustered)} islands (no touching neighbors)"
    )

    rate_cols = []
    skipped_rates = []
    for col in RATE_COLUMNS:
        if _has_variation(clustered[col]):
            rate_cols.append(col)
        else:
            skipped_rates.append(col)

    moran = spatial.morans_i(clustered, w, rate_cols)
    print("Moran's I (clustered):")
    for col, r in moran.items():
        print(f"    {col:18s} I={r['I']:.3f}  E[I]={r['EI']:.3f}  p={r['p_sim']:.3f}")

    # Headline stat for the map: the SOR-alone share is the rate closest to what the
    # node colors show. Guarded with .get() because the variation filter above can
    # legitimately drop pct_HSOR in a degenerate region.
    r = moran.get("pct_HSOR")
    stats_note = (
        f"Moran's I (SOR-alone share, small-population clustering method**): "
        f"{r['I']:.2f} vs. null of {r['EI']:.2f}, p={r['p_sim']:.3f}"
        if r
        else None
    )

    # Get state outlines for plotting the dual graph on top of the state boundaries.
    states = gdf.dissolve(by="STATEFP").to_crs(
        epsg=3857
    )  # Web Mercator units for plotting

    # Dual graph + map, then half-edge scores computed on the graph.
    # print("Clustered is: ", clustered.describe())
    graph = spatial.build_dual_graph(clustered, out_dir / "dual_graph.json")
    viz.plot_dual_graph(
        graph,
        save_path=out_dir / f"{region_name}_dual_graph.html",
        region_name=region_name,
        unit_plural="counties",
        state_outlines=states,
        stats_note=stats_note,
    )

    he_pairs = (
        []
    )  # half-edge pairs that have non-zero counts for both columns; otherwise, CAPY will error out.
    skipped_pairs = []
    for label, x_col, y_col in HALF_EDGE_PAIRS:
        if clustered[x_col].sum() > 0 and clustered[y_col].sum() > 0:
            he_pairs.append((label, x_col, y_col))
        else:
            skipped_pairs.append(label)

    half_edge_scores = {
        label: spatial.half_edge(graph, x_col, y_col)
        for label, x_col, y_col in he_pairs
    }
    print("CAPY half-edge scores:")
    for label, score in half_edge_scores.items():
        print(f"    {label:24s} {score:.3f}")

    # Baseline + Strategy B share the same raw HISPANIC>0 units (no clustering),
    # so raw vs Empirical Bayes isolates the effect of smoothing.
    gdf_eb = gdf[gdf["HISPANIC"] > 0].copy()
    gdf_eb["dem_base"] = gdf_eb["E_20_PRES_DEM"] + gdf_eb["E_20_PRES_REP"] + 1

    eb_specs = []
    skipped_eb = []
    for label, count_col, base_col in EB_SPECS:
        if _has_variation(gdf_eb[count_col] / gdf_eb[base_col]):
            eb_specs.append((label, count_col, base_col))
        else:
            skipped_eb.append(label)

    raw = {
        label: spatial.raw_moran(gdf_eb, count_col, base_col)
        for label, count_col, base_col in eb_specs
    }
    print("Moran's I (raw, no denoising):")
    for label, r in raw.items():
        print(f"    {label:18s} I={r['I']:.3f}  E[I]={r['EI']:.3f}  p={r['p_sim']:.3f}")

    eb = {
        label: spatial.empirical_bayes_moran(gdf_eb, count_col, base_col)
        for label, count_col, base_col in eb_specs
    }
    print("Moran's I (Empirical Bayes):")
    for label, r in eb.items():
        print(f"    {label:18s} I={r['I']:.3f}  E[I]={r['EI']:.3f}  p={r['p_sim']:.3f}")

    # Section README: dual graph + the three result tables (so they don't vanish).
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
    )[
        ["method", "key", "I", "EI", "p_sim"]
    ]  # Keep only these cols
    moran_csv.to_csv(out_dir / f"{region_name}_moran.csv", index=False)
    he_df.to_csv(out_dir / f"{region_name}_half_edge.csv")

    readme = out_dir / "README.md"
    body = (
        "Is Hispanic race choice spatially clustered? A raw baseline plus two "
        "denoising strategies — clustering small units (A) and Empirical-Bayes "
        "smoothing (B) — each scored with Moran's I, plus CAPY half-edge scores "
        "on the cluster dual graph. Positive Moran's I (p≈0.001) = neighboring "
        "units resemble each other. Raw rates are noisy (small Hispanic counts), "
        "which attenuates Moran's I toward 0; raw vs Empirical Bayes uses the "
        "same units, so it isolates the effect of smoothing.\n\n"
        "## Dual graph\n\n"
        + report.embed_figures(
            [out_dir / f"{region_name}_dual_graph.html"], readme.parent
        )
        + "\n\n## Moran's I — raw baseline (no denoising)\n\n"
        + report.df_to_md(raw_df, index_label="rate")
        + "\n\n## Moran's I — clustered (strategy A)\n\n"
        + report.df_to_md(moran_df, index_label="rate")
        + "\n\n## Moran's I — Empirical Bayes (strategy B)\n\n"
        + report.df_to_md(eb_df, index_label="rate")
        + "\n\n## CAPY half-edge scores\n\n"
        + report.df_to_md(he_df, index_label="group")
        + "\n\n## Data files\n\n"
        f"- [`{region_name}_moran.csv`]({region_name}_moran.csv)\n"
        f"- [`{region_name}_half_edge.csv`]({region_name}_half_edge.csv)\n"
    )
    if skipped_rates or skipped_pairs or skipped_eb:
        body += (
            "\n\n## Skipped in this region\n\n"
            "No data or no variation here (e.g. Puerto Rico holds no presidential election):\n\n"
            f"- Moran's I: {skipped_rates}\n"
            f"- Half-edge: {skipped_pairs}\n"
            f"- Raw/EB Moran's I: {skipped_eb}\n"
        )
    report.write_section_readme(readme, "Spatial analysis", body)

    print(f"  wrote dual graph -> {out_dir / f'{region_name}_dual_graph.html'}")
    print(f"  wrote spatial figures -> {out_dir}")
    print(f"  wrote section summary -> {readme}")
