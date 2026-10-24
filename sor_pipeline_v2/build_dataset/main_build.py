"""Build the county or tract dataset: ingest every source, derive every variable.

The build produces two artifacts. `raw.parquet` is the assembled ingest
output, untouched by the derive steps -- every source column as the API or
file delivered it, the audit trail. `processed.parquet` is the derived
frame, restricted to the manifest's declared schema. The derive steps are
pure arithmetic on raw, so everything in between is cheap to recompute.

The two levels differ in three places and nowhere else: tracts are pulled
one state at a time (the API refuses a state wildcard below county level),
their election votes are prorated from VEST precincts rather than read
from a published county table, and their processed schema therefore omits
the two vote-growth features, which would need a 2016 proration as well.
"""

import argparse
from collections.abc import Sequence
from typing import get_args

import pandas as pd
from tqdm import tqdm

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
from build_dataset.ingest.acs import acs_api
from build_dataset.ingest.acs.feats import ACS_FEATURES
from build_dataset.ingest.dhc import dhc_api
from build_dataset.ingest.election import election_api, tract_election_api
from build_dataset.ingest.election.election_feats import ELECTION_FEATURES
from build_dataset.ingest.fetch_and_store import store_df
from build_dataset.ingest.fetch_and_store.census_client import (
    NATIONAL_COUNTIES,
    state_tracts,
)
from build_dataset.ingest.geometry import geometry_api
from build_dataset.ingest.pl import pl_api
from utils import config

# The election features a tract build can actually compute, taken from
# the manifest's own list of what tracts lack so the schema, the derive
# step and any model fit on tracts cannot disagree.
TRACT_ELECTION_FEATURES = [
    feature
    for feature in ELECTION_FEATURES
    if feature.var_name not in feature_manifest.TRACT_ABSENT_VARIABLES
]

# The GerryDB release ships a tract view for the 50 states only. Puerto
# Rico casts no presidential ballots, so it has nothing to publish; DC
# does vote but the release has no tract view for it. Both come out with
# NaN vote columns, exactly as PR's municipios already do in the county
# build. Nothing is derived to fill the gap -- the published tract
# numbers are used as published or not at all.
TRACT_ELECTION_MISSING_STATES = ("11", "72")


def ingest_counties() -> pd.DataFrame:
    """Fetch every county-level source and assemble one frame on the PL spine.

    Every other source is left-joined onto the PL total-population frame's
    GEOIDs, so a county a source is silent about appears with missing
    values rather than disappearing. Each merge prints a ledger line --
    how many spine counties that source left without data -- so a
    coverage surprise shows up in the build output the moment it is
    introduced.

    Returns
    -------
    pandas.DataFrame
        One row per spine county; every source's columns, values as the
        sources delivered them (strings for the census sources).

    Raises
    ------
    ValueError
        If a merge changes the row count -- a source with duplicate
        GEOIDs would silently multiply spine rows.
    """
    pl_total, pl_hispanic = pl_api.fetch_decennial_pl(NATIONAL_COUNTIES)

    sources = [
        ("pl_hispanic", pl_hispanic),
        ("acs", acs_api.load_acs_features(NATIONAL_COUNTIES)),
        ("acs_prior", acs_api.load_acs_prior(NATIONAL_COUNTIES)),
        ("dhc", dhc_api.load_dhc_features(NATIONAL_COUNTIES)),
        ("geometry", geometry_api.load_county_geometry()),
        ("election", election_api.load_county_election()),
    ]

    print(f"spine (pl_total): {len(pl_total)} counties")
    merged, _ = _merge_onto_spine(pl_total, sources, report=True)
    return merged


def _merge_onto_spine(
    spine: pd.DataFrame,
    sources: list[tuple[str, pd.DataFrame]],
    report: bool,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Left-join every source onto the spine, refusing any row-count change.

    Parameters
    ----------
    spine : pandas.DataFrame
        The frame whose GEOIDs define the universe (the PL total-population
        pull at whichever level).
    sources : list of (str, pandas.DataFrame)
        Each source's name and frame; every one must carry GEOID.
    report : bool
        Print a ledger line per source. The county build does; the tract
        build does not, because 52 states would print 260 lines -- it
        totals the counts and prints them once instead.

    Returns
    -------
    tuple of (pandas.DataFrame, dict)
        The merged frame, and how many spine rows each source left without
        data.

    Raises
    ------
    ValueError
        If a merge changes the row count -- a source with duplicate
        GEOIDs would silently multiply spine rows.
    """
    spine_geoids = spine["GEOID"]
    merged = spine
    missing: dict[str, int] = {}
    for source_name, source_df in sources:
        merged = merged.merge(source_df, on="GEOID", how="left")
        if len(merged) != len(spine):
            raise ValueError(
                f"merge with {source_name} changed the row count "
                f"({len(spine)} -> {len(merged)}): duplicate GEOIDs in {source_name}"
            )

        missing[source_name] = int((~spine_geoids.isin(source_df["GEOID"])).sum())
        if report:
            print(
                f"  + {source_name:12s} {len(source_df)} rows -> {missing[source_name]} rows without data"
            )
    return merged, missing


def ingest_tracts(
    state_fips: Sequence[str] = config.TRACT_PULL_STATE_FIPS,
) -> pd.DataFrame:
    """Fetch every tract-level source, one state at a time, and stack them.

    The API refuses a state wildcard below county level, so each state is
    its own pull and its own set of caches; a run interrupted partway
    resumes from the states already cached. Within a state the assembly is
    the county build's: every source left-joined onto that state's PL
    total-population frame.

    The election source is the one that differs from the county build:
    tract returns come from the lab's GerryDB release rather than MEDSL
    (see `tract_election_api`). It is a plain read of a published figure
    per tract, so there is nothing to cache.

    Parameters
    ----------
    state_fips : sequence of str
        Two-digit state FIPS codes to pull; defaults to the 52
        jurisdictions the PL file covers. Pass a single code to build one
        state.

    Returns
    -------
    pandas.DataFrame
        One row per tract across the requested states, sorted by GEOID;
        every source's columns as the sources delivered them.

    Raises
    ------
    ValueError
        Propagated from `_merge_onto_spine` if a source duplicates GEOIDs.
    """
    per_state_dfs: list[pd.DataFrame] = []
    total_missing_tracts: dict[str, int] = {}
    # The postfix names the state being worked on rather than only how
    # many are done, the run being long enough to want that. `progress.write`
    # for the per-state line so it scrolls above the bar instead of
    # through it.
    with tqdm(
        state_fips, total=len(state_fips), desc="states", unit="state"
    ) as progress:
        for fips_code in progress:
            progress.set_postfix(state=fips_code)
            geo_scope = state_tracts(fips_code)
            pl_total, pl_hispanic = pl_api.fetch_decennial_pl(geo_scope)
            sources = [
                ("pl_hispanic", pl_hispanic),
                ("acs", acs_api.load_acs_features(geo_scope)),
                ("acs_prior", acs_api.load_acs_prior(geo_scope)),
                ("dhc", dhc_api.load_dhc_features(geo_scope)),
                ("geometry", geometry_api.load_tract_geometry(fips_code)),
            ]
            if fips_code not in TRACT_ELECTION_MISSING_STATES:
                sources.append(
                    ("election", tract_election_api.load_tract_election(fips_code))
                )
            merged, missing = _merge_onto_spine(pl_total, sources, report=False)
            for source_name, missing_count in missing.items():
                total_missing_tracts[source_name] = (
                    total_missing_tracts.get(source_name, 0) + missing_count
                )
            per_state_dfs.append(merged)
            progress.write(f"  state {fips_code}: {len(merged):,} tracts")

    stacked = pd.concat(per_state_dfs, ignore_index=True)
    print(f"spine (pl_total): {len(stacked)} tracts across {len(state_fips)} states")
    for name, count in total_missing_tracts.items():
        print(f"  + {name:12s} -> {count} tracts without data")
    return stacked


def clean_and_derive_tracts(df: pd.DataFrame) -> pd.DataFrame:
    """Run the derive steps that apply at tract level, in dependency order.

    The county steps, with the election one restricted to the features
    tracts can support (TURNOUT's denominator cannot carry it); see
    `clean_and_derive_counties` for why the order is what it is.

    Parameters
    ----------
    df : pandas.DataFrame
        The assembled tract ingest frame.

    Returns
    -------
    pandas.DataFrame
        The frame with every tract-level derived variable added.

    Raises
    ------
    KeyError
        Propagated from any step whose input columns are absent.
    """
    df = coerce_numeric(df)
    df = clean_and_transform_pl_data(df)
    df = main_acs_clean_and_transform(df, ACS_FEATURES)
    df = add_dhc_derived_features(df)
    df = add_geometry_derived_features(df)
    df = add_election_features(df, TRACT_ELECTION_FEATURES)
    return df


def clean_and_derive_counties(df: pd.DataFrame) -> pd.DataFrame:
    """Run the derive steps in dependency order.

    0. coerce_numeric: strings -> numbers (GEOID and NAME stay text).
    1. PL: count composites, Hispanic-of-race counts, share targets,
       dominant-race classification.
    2. ACS: sentinel nullification, then every declared share and growth.
    3. DHC: URBANSHARE.
    4. Geometry: passthroughs and DENSITY (needs step 1's TOTALPOP).
    5. Election: votes, lean, turnout, growth (TURNOUT needs step 2's
       VOTINGAGEPOP).

    Each step preflights its own inputs and raises a KeyError naming the
    step that should have created them, so order violations fail loudly.

    Parameters
    ----------
    df : pandas.DataFrame
        The assembled ingest frame (`ingest_counties` output or
        raw.parquet reloaded).

    Returns
    -------
    pandas.DataFrame
        The frame with every derived variable added; no rows are ever
        dropped, and raw columns are kept (the manifest selection is what
        trims them).

    Raises
    ------
    KeyError
        Propagated from any step whose input columns are absent.
    """
    df = coerce_numeric(df)
    df = clean_and_transform_pl_data(df)
    df = main_acs_clean_and_transform(df, ACS_FEATURES)
    df = add_dhc_derived_features(df)
    df = add_geometry_derived_features(df)
    df = add_election_features(df)
    return df


def build(
    level: config.GeographicBuildLevel = "national_counties",
    state_fips: Sequence[str] | None = None,
    from_raw: bool = False,
) -> None:
    """Build the requested dataset: raw (as fetched) and processed (analysis-ready).

    Both levels run the same two saves. They differ in what is fetched,
    which election features the derive step computes, and which schema the
    processed frame is cut to.

    Parameters
    ----------
    level : config.GeographicBuildLevel
        "national_counties" or "national_tracts".
    state_fips : sequence of str or None
        Tracts only: which states to pull, defaulting to all 52. Ignored
        for the county build, which is a single national request.
    from_raw : bool
        Re-derive from the raw parquet already on disk instead of
        fetching, and leave that raw file alone. The raw frame holds the
        sources as published, so anything downstream of it -- a renamed
        variable, a new derived feature, a changed formula -- is a pure
        function of a file we already have, and re-fetching it from the
        Census API would be minutes of network for an identical result.
        Fetch (the default) whenever the question is whether the SOURCES
        changed; this flag cannot answer that.

    Raises
    ------
    NotImplementedError
        If `level` is not a config.GeographicBuildLevel.
    KeyError
        If a column the manifest declares is missing from the derived
        frame -- the manifest and the derive stage have drifted apart.
    """
    if level not in get_args(config.GeographicBuildLevel):
        raise NotImplementedError(
            f"Unknown build level: {level!r}; "
            f"known: {list(get_args(config.GeographicBuildLevel))}"
        )

    if level == "national_counties":
        unit = "counties"
        derive = clean_and_derive_counties
        wanted = feature_manifest.processed_columns()
        raw_path = config.RAW_NATIONAL_COUNTIES_PARQUET
        processed_path = config.PROCESSED_NATIONAL_COUNTIES_PARQUET
        ingest = ingest_counties
    else:
        unit = "tracts"
        states = list(state_fips or config.TRACT_PULL_STATE_FIPS)
        derive = clean_and_derive_tracts
        wanted = feature_manifest.processed_columns(
            exclude_variables=feature_manifest.TRACT_ABSENT_VARIABLES
        )
        # Scope-named unless every state was built, so a partial run cannot
        # overwrite the national dataset.
        raw_path, processed_path = config.tract_parquet_paths(states)

        def ingest() -> pd.DataFrame:
            return ingest_tracts(states)

    if from_raw:
        if not raw_path.exists():
            raise FileNotFoundError(
                f"{raw_path} does not exist -- --from-raw re-derives an "
                "existing raw frame and cannot create one; run without it."
            )
        raw = store_df.load_df_from_parquet(raw_path)
        print(f"read raw        {raw.shape[0]} x {raw.shape[1]} <- {raw_path}")
    else:
        raw = ingest().sort_values("GEOID").reset_index(drop=True)
        store_df.save_df_to_parquet(raw, raw_path)
        print(f"saved raw       {raw.shape[0]} x {raw.shape[1]} -> {raw_path}")

    df = derive(raw)
    absent = [c for c in wanted if c not in df.columns]
    if absent:
        raise KeyError(
            f"{len(absent)} processed column(s) missing from the derived "
            f"frame, first few: {absent[:5]} -- the feature_manifest schema and "
            "the clean_and_derive stage have drifted apart."
        )
    processed = df[wanted]
    store_df.save_df_to_parquet(processed, processed_path)
    print(
        f"saved processed {processed.shape[0]} x {processed.shape[1]} "
        f"{unit} -> {processed_path}"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m build_dataset.main_build",
        description="Build the county or tract dataset: raw and processed parquet.",
    )
    parser.add_argument(
        "--level",
        choices=list(get_args(config.GeographicBuildLevel)),
        default="national_counties",
    )
    parser.add_argument(
        "--states",
        nargs="+",
        default=None,
        metavar="FIPS",
        help="tracts only: two-digit state codes to pull (default: all 52)",
    )
    parser.add_argument(
        "--from-raw",
        action="store_true",
        help="re-derive the processed frame from the raw parquet already on "
        "disk, fetching nothing and rewriting no raw file; for changes "
        "downstream of ingestion, such as a renamed or added feature",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    build(level=args.level, state_fips=args.states, from_raw=args.from_raw)
