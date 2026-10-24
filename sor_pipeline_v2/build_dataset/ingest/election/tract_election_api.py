"""Tract-level presidential returns, read from the lab's GerryDB release.

Nothing here is computed. The release publishes a figure per tract for
2016 and 2020, and this module reads those numbers, renames them to the
pipeline's vote columns and stops. Earlier versions of this file
downloaded VEST precincts and TIGER blocks and allocated votes across
them with maup; all of that is gone, because the allocation has already
been done upstream and done once for everybody.

The numbers come from Dave's Redistricting block data (as the release's
own `gerrydb_view_meta` layer records: "obtained from Dave's data in
January of 2025", https://github.com/dra2020/block_data), carried onto
geographies forked from `census.2020/<state>/tract`. So a GEOID here is
an official 2020 census tract GEOID, and it joins the PL spine directly.

Coverage is the 50 states. The release ships no tract view for DC or
Puerto Rico, so neither gets vote columns -- PR casts no presidential
ballots and never had any, and DC's tracts come out NaN exactly as PR's
municipios already do in the county build.

Summing these tracts back up to counties will NOT reproduce
`load_county_election`, and that is not an error. MEDSL publishes some
rows with no county attached -- overseas ballots, statewide write-ins --
and the county loader drops them, so its county totals come up short.
The release has no such category: every vote sits in some block, so
those votes land inside counties here. Check against MEDSL's statewide
total, which counts those rows, not against the sum of its county rows.

Run: `python -m build_dataset.ingest.election.tract_election_api --states 44`
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

from build_dataset.ingest.election.election_feats import (
    DEM_VOTES,
    DEM_VOTES_2016,
    REP_VOTES,
    REP_VOTES_2016,
)
from utils.config import GERRYDB_RELEASE_DIR, STATE_FIPS_TO_USPS

GERRYDB_TRACT_VIEW_TEMPLATE = "{usps}_districtr_tract_view_v2.gpkg"

# GerryDB carries the GEOID in a column called `path` -- the identifier
# the geography was forked under, not a filesystem path.
GERRYDB_GEOID_FIELD = "path"

# Release column -> the pipeline's column.
GERRYDB_PRESIDENTIAL_COLUMNS: dict[str, str] = {
    "pres_16_dem": DEM_VOTES_2016,
    "pres_16_rep": REP_VOTES_2016,
    "pres_20_dem": DEM_VOTES,
    "pres_20_rep": REP_VOTES,
}

TRACT_GEOID_DIGITS = 11


def _tract_view_path(state_fips: str) -> Path:
    """The release file for one state, checked to exist.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.

    Returns
    -------
    Path
        The state's tract-view geopackage.

    Raises
    ------
    KeyError
        If `state_fips` is not a state FIPS code.
    FileNotFoundError
        If the release has no tract view for that state. DC and Puerto
        Rico are the two that legitimately do not; `main_build` lists
        them in TRACT_ELECTION_MISSING_STATES and never asks.
    """
    usps = STATE_FIPS_TO_USPS[state_fips]
    path = GERRYDB_RELEASE_DIR / GERRYDB_TRACT_VIEW_TEMPLATE.format(usps=usps.lower())
    if not path.exists():
        raise FileNotFoundError(
            f"no tract view for state {state_fips} ({usps}) at {path}. The "
            "release ships one per state for the 50 states; DC and Puerto "
            "Rico have none."
        )
    return path


def load_tract_election(state_fips: str) -> pd.DataFrame:
    """One state's presidential votes per tract, as the release publishes them.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.

    Returns
    -------
    pandas.DataFrame
        One row per tract in the state: eleven-digit GEOID plus the four
        vote columns named by GERRYDB_PRESIDENTIAL_COLUMNS.

    Raises
    ------
    FileNotFoundError
        Propagated from `_tract_view_path`.
    KeyError
        If the file lacks a column this reads -- a release whose schema
        has moved, which should fail here rather than silently produce a
        frame with votes missing.
    ValueError
        If the GEOIDs are not distinct eleven-digit codes for this state.
    """
    path = _tract_view_path(state_fips)
    requested = [GERRYDB_GEOID_FIELD, *GERRYDB_PRESIDENTIAL_COLUMNS]
    # ignore_geometry: only the attribute table is wanted, and the
    # geometry is both the bulk of the file and already supplied by
    # geometry_api from TIGER.
    frame = gpd.read_file(
        path, layer=path.stem, columns=requested, ignore_geometry=True
    )

    absent = [column for column in requested if column not in frame.columns]
    if absent:
        raise KeyError(
            f"{path.name} has no column(s) {absent}; it carries "
            f"{sorted(frame.columns)}."
        )

    table = frame[requested].rename(
        columns={GERRYDB_GEOID_FIELD: "GEOID", **GERRYDB_PRESIDENTIAL_COLUMNS}
    )
    table["GEOID"] = table["GEOID"].astype(str)
    _check_geoids(table["GEOID"], state_fips, path.name)
    return table.sort_values("GEOID").reset_index(drop=True)


def _check_geoids(geoids: pd.Series, state_fips: str, label: str) -> None:
    """Fail if the GEOIDs cannot join the PL spine.

    Three ways they could not: the wrong width (a block or block-group
    view read by mistake), a repeat (which would multiply a tract's votes
    on the merge), or another state's codes (a template or USPS mismatch
    pointing at the wrong file).

    Parameters
    ----------
    geoids : pandas.Series
        The GEOID column, as text.
    state_fips : str
        The state the file was asked for.
    label : str
        Filename, for the message.

    Raises
    ------
    ValueError
        If any of the three checks fails.
    """
    widths = sorted(set(geoids.str.len()))
    if widths != [TRACT_GEOID_DIGITS]:
        raise ValueError(
            f"{label}: GEOID widths {widths}, expected "
            f"[{TRACT_GEOID_DIGITS}] -- this is not a tract view."
        )
    repeated = geoids[geoids.duplicated()]
    if not repeated.empty:
        raise ValueError(
            f"{label}: {len(repeated)} repeated GEOID(s), e.g. "
            f"{repeated.iloc[0]}; votes would be double counted on the merge."
        )
    foreign = geoids[~geoids.str.startswith(state_fips)]
    if not foreign.empty:
        raise ValueError(
            f"{label}: {len(foreign)} GEOID(s) outside state {state_fips}, "
            f"e.g. {foreign.iloc[0]}."
        )


def load_tract_election_for_states(state_fips: list[str]) -> pd.DataFrame:
    """Stack `load_tract_election` over several states.

    No caching: the whole 50-state read is well under a second, so a
    cached copy would only be a way for the build to go stale.

    Parameters
    ----------
    state_fips : list of str
        Two-digit state FIPS codes.

    Returns
    -------
    pandas.DataFrame
        One row per tract across the requested states, sorted by GEOID.
    """
    per_state = [load_tract_election(fips) for fips in state_fips]
    return pd.concat(per_state, ignore_index=True).sort_values("GEOID")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m build_dataset.ingest.election.tract_election_api",
        description="Read tract presidential returns from the GerryDB release.",
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
    print(table[list(GERRYDB_PRESIDENTIAL_COLUMNS.values())].sum().to_string())
