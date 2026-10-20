"""Tract-level presidential returns: VEST precincts prorated onto census blocks.

Nobody publishes election results by tract, because precincts are not
census geography and do not nest in tracts. This moves VEST's
precinct-level returns onto tracts in two steps: prorate each precinct's
votes down to 2020 census blocks, weighting each precinct-block overlap by
its share of the precinct's population, then sum blocks into tracts. Only
the first step is modelled -- it assumes voters are spread within a
precinct like residents are. The second is exact, since a block GEOID is
its tract GEOID plus four digits.

The estimate is not a small correction at the edges. 76% of Rhode
Islanders live in a precinct that straddles a tract line, so most votes
get split rather than assigned whole. And within a precinct the split is
modelled rather than measured: two tracts dividing one precinct differ
only by how many people live in each, never by how those people voted.

Summing these tracts back up to counties will NOT reproduce
`load_county_election`, and that is not an error. MEDSL publishes some
rows with no county attached -- overseas ballots, statewide write-ins --
and the county loader drops them, so its county totals come up short.
VEST has no such category: every vote sits in some precinct, so those
votes land inside counties here. Check against MEDSL's statewide total,
which counts those rows, not against the sum of its county rows.

Both downloads cache in RAW_NATIONAL_DIR. The VEST archive is verified
against the MD5 Dataverse publishes, as the MEDSL file is; TIGER blocks
carry no published checksum.

Run: `python -m build_dataset.ingest.election.tract_election_api --states 44`
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import maup
import pandas as pd
import requests
import shapely
from maup.repair import make_valid_polygons
from tqdm import tqdm

from build_dataset.ingest.election.election_feats import DEM_VOTES, REP_VOTES
from build_dataset.ingest.fetch_and_store.dataverse_client import (
    PublishedArchive,
    download_verified,
    published_archive,
)
from utils.config import (
    RAW_NATIONAL_DIR,
    SOURCE_RECORDS_DIR,
    STATE_FIPS_TO_USPS,
)

# Harvard Dataverse VEST 2020 archive -- has the 2020 precinct-level election returns and boundaries.
HARVARD_DATAVERSE_VEST_2020_DOI = "doi:10.7910/DVN/K7760H"
# VEST names one archive per state by lowercase USPS code: ca_2020.zip.
VEST_ARCHIVE_TEMPLATE = "{usps}_2020.zip"
# Named, not inlined, because the checksum manifest declares the raw
# files by name and must not spell these a second time.
VEST_PRECINCT_CACHE_TEMPLATE = "vest_2020_precincts_{state_fips}.zip"
# Which VEST release each archive came from. The fetch verifies the
# bytes against the digest Dataverse publishes and then forgets the
# version, so nothing on disk says WHICH release was verified; a VEST
# version bump would otherwise be invisible after the fact.
VEST_CHECKSUMS_JSON = SOURCE_RECORDS_DIR / "vest_2020_checksums.json"

VEST_PRESIDENTIAL_COLUMNS: dict[str, str] = {
    "G20PREDBID": DEM_VOTES,
    "G20PRERTRU": REP_VOTES,
}

# 2020 tabulation blocks
TIGER_BLOCK_CACHE_TEMPLATE = "tiger_2020_blocks_{state_fips}.zip"
TIGER_BLOCKS_URL = (
    "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/"
    "tl_2020_{state_fips}_tabblock20.zip"
)
# col names for TIGER blocks
BLOCK_GEOID = "GEOID20"
BLOCK_POPULATION = "POP20"

TRACT_ELECTION_PARQUET_TEMPLATE = "tract_election_2020_{state_fips}.parquet"

# A tract GEOID is the first 11 digits of a block GEOID: state(2) +
# county(3) + tract(6).
TRACT_GEOID_DIGITS = 11

# NAD83 Conus Albers: maup's area and containment work wants a projected
# CRS, and both sources arrive in geographic EPSG:4269.
EQUAL_AREA_CRS = 5070

# Repairing a self-intersection should move a boundary, not drastically change a state.
# Oregon's 38 invalid precincts change the layer's total area by 3e-12, so
# anything near this tolerance means the repair did something else.
REPAIR_AREA_TOLERANCE = 1e-6

# Prorating should not introduce discrepancies larger than this tolerance.
VOTE_CONSERVATION_TOLERANCE = 0.5

# How much of the precinct layer's own area two or more precincts both
# claim. Measured: Rhode Island 0, Oregon 1.4e-06, California 4.6e-04.
# Votes conserve exactly at all three -- weights are normalised within
# each precinct -- so this bounds the thing the conservation check
# structurally cannot see: land claimed twice, and so blocks whose
# precinct is ambiguous. A tripwire for a layer that is broken rather
# than merely imperfect, set well clear of California's.
PRECINCT_OVERLAP_AREA_TOLERANCE = 1e-2

# maup.intersections indexes its output ["source", "target"] -- precinct,
# then block.
PRECINCT_LEVEL = 0
BLOCK_LEVEL = 1


# The block of records inside VEST_CHECKSUMS_JSON, named so the file is
# self-describing and can gain top-level fields later -- the same shape as
# the checksum manifest's "files".
VEST_CHECKSUMS_BLOCK = "archives"


@dataclass(frozen=True)
class VestArchiveRecord:
    """One state's VEST archive as the deposit published it.

    `algorithm` and `checksum_value` are spelled as the checksum manifest
    spells them, so it can copy a record across instead of translating
    one. `doi` and `dataset_version` stay structured: the manifest
    flattens them into a prose description, and a version number should
    not have to be parsed back out of a sentence.
    """

    cache_filename: str
    published_filename: str
    doi: str
    dataset_version: str
    checksum_value: str
    recorded: str
    algorithm: str = "md5"


def read_vest_checksums() -> dict[str, dict]:
    """The recorded archives, keyed by state FIPS, or {} if none yet."""
    if not VEST_CHECKSUMS_JSON.exists():
        return {}
    return dict(json.loads(VEST_CHECKSUMS_JSON.read_text())[VEST_CHECKSUMS_BLOCK])


def _record_vest_checksums(
    state_fips: str, dataverse_archive: PublishedArchive
) -> None:
    """Note which VEST release this state's archive was verified against.

    Read-modify-write on one file keyed by state, which is safe only
    because states are fetched in series. Fetching them concurrently
    would need a file per state instead.

    The timestamp is per state rather than one for the file, because
    states are fetched whenever they are first needed and a single
    written-at would misdate every state but the last.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.
    dataverse_archive : PublishedArchive
        The listing entry the download was checked against.
    """
    recorded = read_vest_checksums()
    recorded[state_fips] = asdict(
        VestArchiveRecord(
            cache_filename=VEST_PRECINCT_CACHE_TEMPLATE.format(state_fips=state_fips),
            published_filename=dataverse_archive.filename,
            doi=HARVARD_DATAVERSE_VEST_2020_DOI,
            dataset_version=dataverse_archive.dataset_version,
            checksum_value=dataverse_archive.published_md5,
            recorded=datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
        )
    )
    VEST_CHECKSUMS_JSON.write_text(
        json.dumps({VEST_CHECKSUMS_BLOCK: recorded}, sort_keys=True, indent=2) + "\n"
    )


def _ensure_vest_checksums(state_fips: str, cache: Path) -> None:
    """Reconcile a cached archive with the release record, if it is missing.

    A cache hit skips the fetch that would record the release, so one can
    be missing. The local bytes are verified, not assumed; no listing
    fetch once the entry exists.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.
    cache : Path
        The archive already on disk.

    Raises
    ------
    ValueError
        If the cached bytes do not match the MD5 Dataverse publishes --
        the local copy is not the released file, so no release can be
        recorded for it.
    """
    if state_fips in read_vest_checksums():
        return

    dataverse_archive = published_archive(
        HARVARD_DATAVERSE_VEST_2020_DOI,
        VEST_ARCHIVE_TEMPLATE.format(usps=STATE_FIPS_TO_USPS[state_fips].lower()),
        absent_hint="VEST may not cover this state for 2020.",
    )
    digest = hashlib.md5(cache.read_bytes()).hexdigest()
    if digest != dataverse_archive.published_md5:
        raise ValueError(
            f"{cache.name}: md5 {digest} does not match the checksum Dataverse "
            f"publishes ({dataverse_archive.published_md5}) for dataset version "
            f"{dataverse_archive.dataset_version}; the cached copy is not the "
            "released file, so its checksums cannot be recorded. Delete it to "
            "refetch."
        )
    _record_vest_checksums(state_fips, dataverse_archive)
    print(
        f"  recorded checksums for {cache.name} "
        f"(VEST {HARVARD_DATAVERSE_VEST_2020_DOI} "
        f"v{dataverse_archive.dataset_version}), md5 verified"
    )


def _cached_vest_precincts(state_fips: str) -> Path:
    """Download the state's VEST archive if absent, verifying its published MD5.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.

    Returns
    -------
    Path
        The archive on disk.

    Raises
    ------
    KeyError
        If `state_fips` is not one of the 52 jurisdictions.
    ValueError
        If the downloaded bytes do not match the MD5 Dataverse publishes.
    """
    cache = RAW_NATIONAL_DIR / VEST_PRECINCT_CACHE_TEMPLATE.format(
        state_fips=state_fips
    )
    if cache.exists():
        _ensure_vest_checksums(state_fips, cache)
        return cache

    dataverse_archive = published_archive(
        HARVARD_DATAVERSE_VEST_2020_DOI,
        VEST_ARCHIVE_TEMPLATE.format(usps=STATE_FIPS_TO_USPS[state_fips].lower()),
        absent_hint="VEST may not cover this state for 2020.",
    )
    RAW_NATIONAL_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(download_verified(dataverse_archive))
    _record_vest_checksums(state_fips, dataverse_archive)
    print(
        f"  fetched {dataverse_archive.filename} (VEST {HARVARD_DATAVERSE_VEST_2020_DOI} v{dataverse_archive.dataset_version}), "
        f"md5 verified"
    )
    return cache


def _cached_census_blocks(state_fips: str) -> Path:
    """Download the state's TIGER block archive if absent.

    Note: no checksum available to check from the Census api.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.

    Returns
    -------
    Path
        The archive on disk.
    """
    cache = RAW_NATIONAL_DIR / TIGER_BLOCK_CACHE_TEMPLATE.format(state_fips=state_fips)
    if not cache.exists():
        RAW_NATIONAL_DIR.mkdir(parents=True, exist_ok=True)
        url = TIGER_BLOCKS_URL.format(state_fips=state_fips)
        cache.write_bytes(requests.get(url, timeout=600).content)
        print(f"  fetched {cache.name} ({cache.stat().st_size / 1e6:.0f} MB)")
    return cache


def _read_precincts(archive: Path) -> gpd.GeoDataFrame:
    """The precinct layer, renamed to the pipeline's vote columns.

    Parameters
    ----------
    archive : Path
        A VEST state archive.

    Returns
    -------
    geopandas.GeoDataFrame
        One row per precinct: the two vote columns and geometry, projected
        to EQUAL_AREA_CRS.

    Raises
    ------
    KeyError
        If the archive lacks a presidential column VEST is expected to
        publish -- the naming convention has changed for this state.
    """
    with zipfile.ZipFile(archive) as zipped:
        shapefile = next(n for n in zipped.namelist() if n.endswith(".shp"))
    frame = gpd.read_file(f"{archive}!{shapefile}")

    absent = [c for c in VEST_PRESIDENTIAL_COLUMNS if c not in frame.columns]
    if absent:
        raise KeyError(
            f"{archive.name} has no column(s) {absent}; VEST's naming differs "
            f"for this state. Present presidential columns: "
            f"{[c for c in frame.columns if c.startswith('G20PRE')]}"
        )
    frame = frame.rename(columns=VEST_PRESIDENTIAL_COLUMNS)
    kept = [*VEST_PRESIDENTIAL_COLUMNS.values(), "geometry"]
    precincts = gpd.GeoDataFrame(frame[kept]).to_crs(EQUAL_AREA_CRS)
    return _make_geometries_valid(precincts, archive.name)


def _make_geometries_valid(frame: gpd.GeoDataFrame, label: str) -> gpd.GeoDataFrame:
    """Fix self-intersections and degenerate rings, leaving topology alone.

    A source layer's polygons are not all valid, and an invalid one makes
    GEOS raise `TopologyException: side location conflict` the moment maup
    intersects it. This repairs each polygon in isolation.

    It deliberately does NOT repair topology BETWEEN polygons. Overlaps
    and holes are the source's own boundaries, so resolving them moves
    precinct lines rather than fixing broken ones -- and they cost nothing
    here, because weights are normalised within each precinct: a
    precinct's total is shared out across whatever it overlaps, however
    the overlaps fall, so no vote can be lost either way.

    Which is why maup's two published repair functions are the wrong
    tools. `quick_repair` is make_valid, then `resolve_overlaps`, then
    `close_gaps`; only the first step is wanted. `resolve_overlaps` awards
    contested area to whichever polygon shares the most perimeter with it,
    a tie-break rather than a recovered boundary, and its default
    relative_threshold then leaves any overlap above a tenth of either
    polygon's area alone -- declining the cases that could matter while
    moving the slivers that do not. `smart_repair` was measured at 987s
    per state, left `maup.doctor` still reporting the layer unclean, and
    moved more of the layer's area than the defect it was repairing.

    `make_valid_polygons` is maup's validity-only repair, and is what
    this uses. It is imported from `maup.repair` because
    `maup/__init__.py` re-exports its siblings and not it; depending on an
    unexported name is worth it here because it was measured to agree with
    shapely's `make_valid(method="structure")` -- same validity outcome,
    same area drift, fourteen of a state's polygons differing by a
    combined fraction of a square millimetre -- and because its going away
    would be an ImportError at module load rather than a silent change in
    the result. What maup does not provide, at any entry point, is a check
    that a repair moved a boundary instead of resizing the layer, which is
    what the area assertion below is for.

    Parameters
    ----------
    frame : geopandas.GeoDataFrame
        Any polygon layer.
    label : str
        Name used in the reported line, e.g. the archive's filename.

    Returns
    -------
    geopandas.GeoDataFrame
        The same rows with every geometry valid; unchanged and uncopied if
        all were already valid.

    Raises
    ------
    ValueError
        If repair changed the layer's total area by more than
        REPAIR_AREA_TOLERANCE, which would mean it did more than close a
        self-intersection.
    """
    shapes = frame.geometry
    invalid = ~shapes.is_valid
    if not invalid.any():
        return frame

    area_before = shapes.area.sum()
    repaired_frame = frame.copy()

    # force_polygons keeps polygonal input polygonal: plain make_valid can
    # return a GeometryCollection, which maup cannot read.
    repaired_frame["geometry"] = make_valid_polygons(shapes, force_polygons=True)
    repaired_shapes = repaired_frame.geometry
    area_drift = (repaired_shapes.area.sum() - area_before) / area_before
    if abs(area_drift) > REPAIR_AREA_TOLERANCE:
        raise ValueError(
            f"{label}: repairing {int(invalid.sum())} invalid geometries changed "
            f"the layer's total area by {area_drift:+.2e}, beyond the "
            f"{REPAIR_AREA_TOLERANCE:.0e} tolerance; inspect before trusting it."
        )
    print(
        f"  repaired {int(invalid.sum())} invalid geometries in {label} "
        f"(total area change {area_drift:+.1e})"
    )
    return repaired_frame


def _report_overlap_area(precincts: gpd.GeoDataFrame, label: str) -> None:
    """Report what share of the precinct layer more than one precinct claims.

    This replaces `maup.doctor`, which costs 58s per state on California
    to return a bool that cannot change: invalid geometries are already
    repaired by this point, and the overlaps and holes it would also find
    are VEST's own boundaries, accepted by policy. Of what it measures,
    only the overlaps are unaccounted for elsewhere -- a block sitting in
    a precinct gap turns up in the stranded-residents warning below,
    which counts people rather than land.

    Parameters
    ----------
    precincts : geopandas.GeoDataFrame
        The repaired precinct layer, in an equal-area CRS.
    label : str
        Name used in the reported line, e.g. the archive's filename.
    """
    shapes = precincts.geometry
    union_area = shapely.union_all(shapes.to_numpy()).area

    overlap_share = max(0.0, shapes.area.sum() - union_area) / union_area
    print(
        f"  {label}: {overlap_share:.1e} of the precinct layer's area is "
        "claimed more than once"
    )
    if overlap_share > PRECINCT_OVERLAP_AREA_TOLERANCE:
        print(
            f"  WARNING: that is beyond the {PRECINCT_OVERLAP_AREA_TOLERANCE:.0e} "
            "tolerance. Votes still conserve, but which precinct a block "
            "belongs to is ambiguous across that much of the state."
        )


def _read_blocks(archive: Path) -> gpd.GeoDataFrame:
    """The block layer: GEOID, population, geometry, projected.

    Parameters
    ----------
    archive : Path
        A TIGER TABBLOCK20 state archive.

    Returns
    -------
    geopandas.GeoDataFrame
        One row per block, projected to EQUAL_AREA_CRS.
    """
    frame = gpd.read_file(archive)
    cols_to_keep = [BLOCK_GEOID, BLOCK_POPULATION, "geometry"]
    blocks = gpd.GeoDataFrame(frame[cols_to_keep]).to_crs(EQUAL_AREA_CRS)
    return _make_geometries_valid(blocks, archive.name)


def _population_weights(
    overlap_shapes: gpd.GeoSeries, blocks: gpd.GeoDataFrame
) -> pd.Series:
    """Each precinct-block overlap's share of its precinct's population.

    `maup.prorate` does not normalise: it multiplies a precinct's votes by
    the weight it is handed, so the weights of one precinct's overlaps
    have to sum to 1. `maup.normalize` is what does that.

    An overlap's population is its block's, scaled by the fraction of
    the block the overlap covers -- the same even-spread assumption the
    module docstring describes, applied one level further down.

    Parameters
    ----------
    overlap_shapes : geopandas.GeoSeries
        `maup.intersections(precincts, blocks)`: a MultiIndex of
        ("source", "target") over precinct and block labels.
    blocks : geopandas.GeoDataFrame
        The block layer, carrying BLOCK_POPULATION.

    Returns
    -------
    pandas.Series
        Weights indexed like `overlap_shapes`, summing to 1 within each
        precinct.
    """
    block_shapes = blocks.geometry
    block_of_each_overlap = overlap_shapes.index.get_level_values(BLOCK_LEVEL)

    block_population = blocks[BLOCK_POPULATION]

    # reindex onto the overlap index rather than Index.map: the stubs type
    # a mapper as a renamer and reject a Series outright.
    whole_block_area = block_shapes.area.reindex(block_of_each_overlap).to_numpy()
    whole_block_population = block_population.reindex(block_of_each_overlap).to_numpy()

    fraction_of_block = overlap_shapes.area.to_numpy() / whole_block_area
    overlap_population = pd.Series(
        whole_block_population * fraction_of_block,
        index=overlap_shapes.index,
    )

    precinct_has_residents = overlap_population.groupby(level=PRECINCT_LEVEL).sum() > 0
    overlap_has_residents = precinct_has_residents.reindex(
        overlap_shapes.index.get_level_values(PRECINCT_LEVEL)
    ).to_numpy()
    if not overlap_has_residents.all():
        print(
            f"  {int((~precinct_has_residents).sum())} precinct(s) enclose no "
            "residents; their votes were spread by area instead of population."
        )

    weights_by_population = maup.normalize(overlap_population, level=PRECINCT_LEVEL)
    weights_by_area = maup.normalize(overlap_shapes.area, level=PRECINCT_LEVEL)
    return weights_by_population.where(overlap_has_residents, weights_by_area)


def load_tract_election(state_fips: str) -> pd.DataFrame:
    """One state's presidential votes, prorated to blocks and summed to tracts.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.

    Returns
    -------
    pandas.DataFrame
        One row per tract that contains at least one block: eleven-digit
        GEOID plus the two vote columns, as floats (proration does not
        yield whole votes, and the values are deliberately not rounded --
        rounding at block level accumulates error on the way up).

    Raises
    ------
    ValueError
        If prorating loses or invents votes.
    KeyError
        Propagated from `_read_precincts` on an unexpected VEST schema.
    """
    precincts = _read_precincts(_cached_vest_precincts(state_fips))
    blocks = _read_blocks(_cached_census_blocks(state_fips))

    _report_overlap_area(precincts, f"state {state_fips}")

    vote_columns = list(VEST_PRESIDENTIAL_COLUMNS.values())

    overlap_shapes = maup.intersections(precincts, blocks)
    assert isinstance(overlap_shapes, gpd.GeoSeries)
    prorated = maup.prorate(
        overlap_shapes,
        precincts[vote_columns],
        _population_weights(overlap_shapes, blocks),
    )

    # prorate emits a row only for a block some precinct reaches; a block
    # lying entirely in a gap between precincts gets none. Those blocks
    # hold no votes, but they do belong to tracts, and dropping them would
    # drop whole tracts (Oregon's six water tracts) from the output.
    on_blocks = prorated.reindex(blocks.index).fillna(0.0)
    unreached = blocks.index.difference(prorated.index)
    stranded = blocks.loc[unreached, BLOCK_POPULATION].sum()
    if stranded:
        print(
            f"  WARNING: {int(stranded):,} residents sit in blocks no precinct "
            "reaches; their share of the vote cannot be placed."
        )

    for column in vote_columns:
        before, after = precincts[column].sum(), on_blocks[column].sum()
        if abs(before - after) > VOTE_CONSERVATION_TOLERANCE:
            raise ValueError(
                f"{column}: {before:,} votes in precincts became {after:,.1f} on "
                "blocks; proration lost or invented votes."
            )

    # Exact: blocks nest in tracts by construction of the GEOID.
    tract = blocks[BLOCK_GEOID].str[:TRACT_GEOID_DIGITS]
    tracts = on_blocks.join(tract.rename("tract")).groupby("tract")[vote_columns].sum()
    # A column-list key leaves the stubs with a scalar union; grouping a
    # list of columns always yields a frame.
    return tracts.rename_axis("GEOID").reset_index()


def cached_tract_election(state_fips: str) -> pd.DataFrame:
    """One state's prorated tract table, computed once and then reread.

    Delete the file to force a recomputation.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.

    Returns
    -------
    pandas.DataFrame
        As `load_tract_election` returns it.
    """
    cache = RAW_NATIONAL_DIR / TRACT_ELECTION_PARQUET_TEMPLATE.format(
        state_fips=state_fips
    )
    if cache.exists():
        return pd.read_parquet(cache)

    table = load_tract_election(state_fips)
    RAW_NATIONAL_DIR.mkdir(parents=True, exist_ok=True)
    table.to_parquet(cache, index=False)
    print(f"  cached {len(table):,} tracts -> {cache.name}")
    return table


def load_tract_election_for_states(state_fips: list[str]) -> pd.DataFrame:
    """Stack `cached_tract_election` over several states.

    Parameters
    ----------
    state_fips : list of str
        Two-digit state FIPS codes.

    Returns
    -------
    pandas.DataFrame
        One row per tract across the requested states, sorted by GEOID.
    """
    per_state = []
    for fips in tqdm(state_fips, total=len(state_fips), desc="Processing states"):
        frame = cached_tract_election(fips)
        print(f"  {len(frame):,} tracts")
        per_state.append(frame)
    return pd.concat(per_state, ignore_index=True).sort_values("GEOID")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m build_dataset.ingest.election.tract_election_api",
        description="Prorate VEST precinct returns onto census tracts.",
    )
    parser.add_argument(
        "--states",
        nargs="+",
        required=True,
        metavar="FIPS",
        help="two-digit state FIPS codes",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    table = load_tract_election_for_states(args.states)
    print(f"\n{len(table):,} tracts")
    print(table.head().to_string(index=False))
    print(table[[DEM_VOTES, REP_VOTES]].sum().to_string())
