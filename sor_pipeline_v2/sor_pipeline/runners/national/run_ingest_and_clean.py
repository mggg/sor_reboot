from __future__ import annotations
from ...utils import config
from ...ingest import census_api, geometry, election, store
from ...clean import merge, features
import pandas as pd


def run_ingest_and_clean() -> pd.DataFrame:
    """Run the ingest and clean pipeline.

    This is the first step in the SOR pipeline. It fetches data from the Census API and
    election CSVs, merges them, computes features, and saves the result as a Parquet file.
    """
    print("Running ingest and clean pipeline...")
    print(f"  fetching data from Census API and election CSVs...")
    for_geo, in_geo = "county:*", "state:*"
    pl_total, pl_hispanic = census_api.fetch_decennial_pl(for_geo, in_geo)
    acs = census_api.fetch_acs(for_geo, in_geo)
    geo = geometry.load_county_geometry()
    elec = election.load_county_election()

    df = merge.merge_sources(pl_total, pl_hispanic, acs, geo, elec, level="county")
    df = features.add_race_percentages(df)
    df = features.add_ratios(df)
    df = features.add_dominant_race_choice(df)
    df = features.add_hispanic_race_counts(df)
    store.save(df, config.PARQUET_PATH)
    print(f"  wrote {len(df):,} rows -> {config.PARQUET_PATH}")
    return df
