import pandas as pd

from build_dataset.ingest.pl import pl_api
from build_dataset.ingest.acs import acs_api
from build_dataset.ingest.dhc import dhc_api
from build_dataset.ingest.geometry import geometry_api
from build_dataset.ingest.election import election_api
from build_dataset.ingest import store
from build_dataset.clean import coerce
from build_dataset.clean import pl as clean_pl
from build_dataset.clean import acs as clean_acs
from build_dataset.clean import dhc as clean_dhc
from build_dataset.clean import geometry as clean_geometry
from build_dataset.clean import election as clean_election
from build_dataset import manifest
from utils import config

# The attribute columns kept from the TIGER shapefile; the polygons themselves
# stay behind (nothing downstream models geometry, and keeping them would drag
# geopandas through the whole pipeline).
GEOMETRY_ATTRS = ["GEOID", "NAME", "ALAND", "INTPTLAT", "INTPTLON"]


def ingest_counties() -> pd.DataFrame:
    """Fetch every county-level source and assemble one frame on the PL spine.

    PL defines the universe: it carries the targets and the weight column, so
    a unit without PL data has nothing to predict. Every other source joins
    LEFT onto it -- a source that lacks a county costs that county NaNs in
    that source's columns, never its row. Deciding what to do about the NaNs
    is the model layer's job, where the decision is visible and reported;
    ingest only records what each source says, silences included.

    Known silences at county level: the 2011-2015 ACS lacks Chugach and
    Copper River, AK (created in the 2019 Valdez-Cordova split), and the
    election file lacks Puerto Rico (no presidential vote).
    """
    for_geo, in_geo = "county:*", "state:*"
    pl_total, pl_hispanic = pl_api.fetch_decennial_pl(for_geo, in_geo)

    sources = [
        ("pl_hispanic", pl_hispanic),
        ("acs", acs_api.fetch_acs_features(for_geo, in_geo)),
        ("acs_prior", acs_api.fetch_acs_prior(for_geo, in_geo)),
        ("dhc", dhc_api.fetch_dhc(for_geo, in_geo)),
        ("geometry", geometry_api.load_county_geometry()[GEOMETRY_ATTRS]),
        ("election", election_api.load_county_election()),
    ]

    merged = pl_total  # the spine
    print(f"spine (pl_total): {len(merged)} counties")
    for name, frame in sources:
        merged = merged.merge(frame, on="GEOID", how="left")
        # A left join cannot shrink the spine, but a source with duplicate
        # GEOIDs would silently GROW it (one spine row matching two source
        # rows becomes two rows).
        if len(merged) != len(pl_total):
            raise ValueError(
                f"merge with {name} changed the row count "
                f"({len(pl_total)} -> {len(merged)}): duplicate GEOIDs in {name}"
            )
        # The ledger: how many spine counties this source is silent about.
        probe = next(c for c in frame.columns if c != "GEOID")
        print(
            f"  + {name:12s} {len(frame)} rows -> {merged[probe].isna().sum()} counties without data"
        )

    return merged


def clean_counties(df: pd.DataFrame) -> pd.DataFrame:
    """Steps 0-5, in dependency order (each step asserts what it needs)."""
    df = coerce.coerce_numeric(df)          # 0: strings -> numbers
    df = clean_pl.add_targets(df)           # 1: renames, composites, targets, weight
    df = clean_acs.add_acs_features(df)     # 2: 87 shares, derived, growth, auxiliaries
    df = clean_dhc.add_dhc_features(df)     # 3: URBANSHARE
    df = clean_geometry.add_geometry_features(df)  # 4: DENSITY (needs step 1)
    df = clean_election.add_election_features(df)  # 5: votes (needs step 2)
    return df


def build(build_type: str):
    """Build the requested dataset: raw (as fetched) and processed (analysis-ready).

    `raw.parquet` is the assembled ingest output, untouched by clean -- every
    source column as the API/file delivered it, the audit trail. `processed.parquet`
    is the analysis-ready selection defined by `manifest.processed_columns()`:
    identifiers, named counts, targets, the model features, diagnostics. Clean
    is pure arithmetic on raw, so anything in between is cheap to recompute.
    """
    if build_type == "national_counties":
        out_dir = config.DATA_DIR / "national_counties"
        raw = ingest_counties().sort_values("GEOID")
        store.save_df_to_parquet(raw, out_dir / "raw.parquet")
        print(f"saved raw       {raw.shape[0]} x {raw.shape[1]} -> {out_dir / 'raw.parquet'}")

        df = clean_counties(raw)
        wanted = manifest.processed_columns("county")
        absent = [c for c in wanted if c not in df.columns]
        if absent:
            raise KeyError(
                f"{len(absent)} processed column(s) missing from the cleaned "
                f"frame, first few: {absent[:5]} -- the manifest schema and the "
                "clean stage have drifted apart."
            )
        processed = df[wanted]
        store.save_df_to_parquet(processed, out_dir / "processed.parquet")
        print(f"saved processed {processed.shape[0]} x {processed.shape[1]} -> {out_dir / 'processed.parquet'}")
    else:
        raise NotImplementedError(f"Unknown build type: {build_type}")


if __name__ == "__main__":
    build("national_counties")
