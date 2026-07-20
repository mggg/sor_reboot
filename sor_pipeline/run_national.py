from sor_pipeline.utils import config, checkpoint
from sor_pipeline.runners.national.run_ingest_and_clean import run_ingest_and_clean
from sor_pipeline.ingest import store
from sor_pipeline.runners.national.run_scatter_figures import run_scatter_figures
from sor_pipeline.runners.national.run_pearson_correlations import (
    run_pearson_correlations,
)
from sor_pipeline.runners.national.run_spatial_analysis import run_spatial_analysis


def main() -> None:
    config.NATIONAL_DIR.mkdir(parents=True, exist_ok=True)

    # All analysis outputs land in a parameter-keyed run directory; stamp it with
    # a README recording the config so each run is self-describing.
    config.write_run_readme()
    print(f"Run outputs -> {config.NATIONAL_RUN_DIR}")

    # --- Step 1: build the processed dataset (ingest -> clean -> features) ---
    if checkpoint.confirm_rerun(config.PARQUET_PATH, "build dataset"):
        df = run_ingest_and_clean()
    else:
        print(f"Skipping dataset build; {config.PARQUET_PATH} already exists.")
        df = store.load(config.PARQUET_PATH)

    # --- Step 2: scatter figures ---
    if checkpoint.confirm_rerun(config.NATIONAL_SCATTER_DIR, "scatter figures"):
        run_scatter_figures(df)

    # --- Step 3: Pearson correlations of the race-to-Hispanic ratios + scatter section README ---
    if checkpoint.confirm_rerun(config.CORRELATIONS_PATH, "correlations"):
        run_pearson_correlations(df)

    # --- Step 4: spatial analysis (clustering -> Moran's I, half-edge, dual graph) ---
    regions = config.REGIONS.keys()
    paths = [config.NATIONAL_SPATIAL_DIR / region for region in regions]
    regions_to_run = list(regions)
    for path, region in zip(paths, regions):
        if not checkpoint.confirm_rerun(path, f"spatial analysis for {region}"):
            regions_to_run.remove(region)
    run_spatial_analysis(df, include_regions=regions_to_run)


if __name__ == "__main__":
    main()
