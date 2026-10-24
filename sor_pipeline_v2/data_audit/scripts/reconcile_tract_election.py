"""Audit: do the release's tract votes reconcile with the published canvass?

The tract election path (the lab's GerryDB release, built from Dave's
Redistricting block data) shares no code and no source file with the
county path (MEDSL). That makes MEDSL an independent channel, and this
script is the comparison -- the same principle as the layer-1 scripts,
applied to a geography nobody canvasses. It matters more now than it did
when the tract figures were ours: this is the only check that the numbers
we have adopted are the ones the states actually certified.

Two checks, because they answer different questions:

  STATEWIDE, against MEDSL's total INCLUDING its FIPS-less reporting units
  (overseas and military ballots, statewide write-ins, Rhode Island's
  federal precinct). This should match essentially exactly: the release
  and MEDSL are independent compilations of the same canvass, so a
  disagreement here is a real sourcing difference worth chasing.

  BY COUNTY, against the county loader's output. This is EXPECTED to
  differ, by exactly the FIPS-less votes: `load_county_election` drops
  rows with no county FIPS, while the release has every vote sitting in
  some block. The check reports the gap and whether it is explained by
  those units, rather than pretending the two levels should agree.

A state that passes both is done. A state that fails the statewide check
has a quirk -- a precinct-matching problem upstream, a mode the two
compilations treat differently -- and needs looking at before its tracts
are trusted.

Run: `python -m data_audit.scripts.reconcile_tract_election --states 44 25`
"""

from __future__ import annotations

import argparse

import pandas as pd

from build_dataset.ingest.election.election_api import MEDSL_COUNTY_RAW_CSV
from build_dataset.ingest.election.election_feats import DEM_VOTES, REP_VOTES
from build_dataset.ingest.election.tract_election_api import load_tract_election
from utils.config import RAW_NATIONAL_DIR, STATE_FIPS_TO_USPS

# MEDSL's own column spellings, used only here and in the county loader.
MEDSL_PARTIES = {"DEMOCRAT": DEM_VOTES, "REPUBLICAN": REP_VOTES}
# A vote of slack per column for float summation over ~10^5 blocks.
VOTE_TOLERANCE = 1.0


def medsl_state_rows(state_fips: str) -> pd.DataFrame:
    """Every MEDSL 2020 presidential row for one state, FIPS-less included.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.

    Returns
    -------
    pandas.DataFrame
        The filtered rows, with `county_fips` as a nullable string so the
        FIPS-less reporting units stay visible rather than being coerced.
    """
    frame = pd.read_csv(
        RAW_NATIONAL_DIR / MEDSL_COUNTY_RAW_CSV, dtype={"county_fips": "string"}
    )
    rows = frame[
        (frame["year"] == 2020)
        & (frame["state_po"] == STATE_FIPS_TO_USPS[state_fips])
        & (frame["office"] == "US PRESIDENT")
        & frame["party"].isin(MEDSL_PARTIES)
    ]
    # TOTAL rows supersede vote-mode splits; summing both double-counts.
    has_total = rows.groupby("county_name")["mode"].transform(
        lambda modes: (modes == "TOTAL").any()
    )
    kept = rows[~has_total | (rows["mode"] == "TOTAL")]
    return kept


def _party_totals(rows: pd.DataFrame) -> dict[str, float]:
    """Votes per pipeline column name, from MEDSL rows."""
    by_party = rows.groupby("party")["candidatevotes"].sum()
    # to_dict() rather than Series.get(): the stubs widen a Series element
    # to Scalar, which float() will not take.
    totals = by_party.to_dict()
    return {
        column: float(totals.get(party, 0)) for party, column in MEDSL_PARTIES.items()
    }


def reconcile_state(state_fips: str) -> dict[str, object]:
    """Compare one state's prorated tract votes against MEDSL.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.

    Returns
    -------
    dict
        The state, its tract count, the statewide deltas against MEDSL's
        full total, the FIPS-less vote counts, whether the county-level
        gap is explained by them, and a pass/fail verdict.
    """
    tracts = load_tract_election(state_fips)
    rows = medsl_state_rows(state_fips)

    # Each party's prorated statewide total, taken once.
    tract_totals: dict[str, float] = {}
    for column in MEDSL_PARTIES.values():
        votes = tracts[column]
        tract_totals[column] = float(votes.sum())

    without_fips = rows[rows["county_fips"].isna()]
    with_fips = rows[rows["county_fips"].notna()]

    everything = _party_totals(rows)
    fipsless = _party_totals(without_fips)

    statewide_delta = {
        column: tract_totals[column] - everything[column]
        for column in MEDSL_PARTIES.values()
    }
    passed = all(abs(d) <= VOTE_TOLERANCE for d in statewide_delta.values())

    # The county-level gap should equal the FIPS-less votes exactly.
    county_only = _party_totals(with_fips)
    county_gap = {
        column: tract_totals[column] - county_only[column]
        for column in MEDSL_PARTIES.values()
    }
    gap_explained = all(
        abs(county_gap[column] - fipsless[column]) <= VOTE_TOLERANCE
        for column in MEDSL_PARTIES.values()
    )

    return {
        "state": state_fips,
        "usps": STATE_FIPS_TO_USPS[state_fips],
        "tracts": len(tracts),
        "statewide_delta": statewide_delta,
        "fipsless": fipsless,
        "county_gap_explained": gap_explained,
        "verdict": "match" if passed else "MISMATCH",
    }


def _print_finding(finding: dict[str, object]) -> None:
    """One state's result, as a short block."""
    delta = finding["statewide_delta"]
    fipsless = finding["fipsless"]
    assert isinstance(delta, dict) and isinstance(fipsless, dict)
    print(
        f"\n{finding['usps']} (state {finding['state']}): {finding['tracts']:,} tracts "
        f"-- {finding['verdict']}"
    )
    for column in MEDSL_PARTIES.values():
        print(
            f"  {column:14s} statewide delta vs MEDSL total {delta[column]:+,.1f}"
            f"   FIPS-less units hold {fipsless[column]:,.0f}"
        )
    print(
        f"  county-level gap explained by the FIPS-less units: "
        f"{finding['county_gap_explained']}"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m data_audit.scripts.reconcile_tract_election",
        description="Do prorated tract votes reconcile with the published canvass?",
    )
    parser.add_argument(
        "--states",
        nargs="+",
        required=True,
        metavar="FIPS",
        help="two-digit FIPS codes",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    findings = [reconcile_state(fips) for fips in args.states]
    for finding in findings:
        _print_finding(finding)

    failed = [str(f["usps"]) for f in findings if f["verdict"] != "match"]
    print(f"\n{len(findings) - len(failed)} of {len(findings)} states reconcile")
    if failed:
        print(f"needs review: {', '.join(failed)}")
