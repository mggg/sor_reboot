import pandas as pd

from build_dataset import feature_manifest
from build_dataset.clean_and_derive.clean_and_derive_acs import (
    main_acs_clean_and_transform,
)
from build_dataset.clean_and_derive.clean_and_derive_pl import (
    clean_and_transform_pl_data,
)
from build_dataset.clean_and_derive.coerce_numeric import coerce_numeric
from build_dataset.clean_and_derive.derive_dhc_feats import add_dhc_derived_features
from build_dataset.clean_and_derive.derive_election_feats import add_election_features
from build_dataset.clean_and_derive.derive_geometry_feats import (
    add_geometry_derived_features,
)
from build_dataset.ingest import store_df
from build_dataset.ingest.acs import acs_api
from build_dataset.ingest.acs.feats import ACS_FEATURES
from build_dataset.ingest.dhc import dhc_api
from build_dataset.ingest.election import election_api
from build_dataset.ingest.geometry import geometry_api
from build_dataset.ingest.pl import pl_api
from utils import config


def ingest_counties() -> pd.DataFrame:
    """Fetch every county-level source and assemble one frame on the PL spine."""
    for_geo, in_geo = "county:*", "state:*"
    pl_total, pl_hispanic = pl_api.fetch_decennial_pl(for_geo, in_geo)

    sources = [
        ("pl_hispanic", pl_hispanic),
        ("acs", acs_api.fetch_acs_features(for_geo, in_geo)),
        ("acs_prior", acs_api.fetch_acs_prior(for_geo, in_geo)),
        ("dhc", dhc_api.fetch_dhc(for_geo, in_geo)),
        ("geometry", geometry_api.load_county_geometry()),
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


def clean_and_derive_counties(df: pd.DataFrame) -> pd.DataFrame:
    """Steps 0-5, in dependency order (each step asserts what it needs)."""
    df = coerce_numeric(df)  # 0: strings -> numbers
    df = clean_and_transform_pl_data(df)  # 1: renames, composites, targets
    df = main_acs_clean_and_transform(df, ACS_FEATURES)  # 2: shares + growth
    df = add_dhc_derived_features(df)  # 3: URBANSHARE
    df = add_geometry_derived_features(df)  # 4: DENSITY (needs step 1's TOTALPOP)
    df = add_election_features(df)  # 5: votes (needs step 2's VOTINGAGEPOP)
    return df


def build(build_type: str):
    """Build the requested dataset: raw (as fetched) and processed (analysis-ready).

    `raw.parquet` is the assembled ingest output, untouched by the derive
    steps -- every source column as the API/file delivered it, the audit
    trail. `processed.parquet` is the derived frame. The steps are pure
    arithmetic on raw, so anything in between is cheap to recompute.
    """
    if build_type == "national_counties":
        out_dir = config.DATA_DIR / "national_counties"
        raw = ingest_counties().sort_values("GEOID")
        store_df.save_df_to_parquet(raw, out_dir / "raw.parquet")
        print(
            f"saved raw       {raw.shape[0]} x {raw.shape[1]} -> {out_dir / 'raw.parquet'}"
        )

        df = clean_and_derive_counties(raw)
        wanted = feature_manifest.processed_columns()
        absent = [c for c in wanted if c not in df.columns]
        if absent:
            raise KeyError(
                f"{len(absent)} processed column(s) missing from the derived "
                f"frame, first few: {absent[:5]} -- the feature_manifest schema and "
                "the clean_and_derive stage have drifted apart."
            )
        processed = df[wanted]
        store_df.save_df_to_parquet(processed, out_dir / "processed.parquet")
        print(
            f"saved processed {processed.shape[0]} x {processed.shape[1]} -> {out_dir / 'processed.parquet'}"
        )
    else:
        raise NotImplementedError(f"Unknown build type: {build_type}")


if __name__ == "__main__":
    build("national_counties")
