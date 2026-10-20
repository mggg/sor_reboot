"""Election audit, value check: county_level_2020.csv vs MEDSL returns.

The transit check (compare_election_to_source) proved raw.parquet mirrors
the source CSV; this one asks whether the source CSV's 2020 presidential
vote counts are RIGHT, by comparing them against the MIT Election Data +
Science Lab county returns -- an independent compilation of official
state canvasses sharing nothing with DRA's precinct-allocation pipeline.

Exact equality is NOT the expectation: the source's DRA lineage allocates
precinct returns to census blocks and re-aggregates, so single-digit vote
deltas are the documented norm. Statuses:
  match             delta == 0
  allocation_delta  0 < |delta| <= ALLOCATION_TOLERANCE_VOTES
  needs_review      larger deltas, for human judgment (in practice these
                    concentrate where MEDSL has known reporting gaps,
                    e.g. New York late-counted absentees)
  both_missing      Puerto Rico: no presidential vote in either file
  row_absent        in the source but not MEDSL (Kalawao, HI -- reports
                    through Maui and is absent from MEDSL)

Known jurisdiction quirks handled below: Kansas City, MO reports
separately from its counties (MEDSL pseudo-FIPS 2938000) and is folded
into Jackson County to match census geography; Alaska is excluded because
MEDSL reports its election districts, which do not map to the census
boroughs the pipeline uses; Rhode Island's fips-less FEDERAL PRECINCT
rows are dropped.

Run from sor_pipeline_v2:
  uv run python -m feature_audit.scripts.compare_election_to_medsl
"""

import csv
from collections import Counter
from dataclasses import asdict, fields

import pandas as pd

from data_audit.config import (
    MEDSL_CSV,
    MEDSL_FINDINGS_CSV,
)
from data_audit.findings import AuditFinding, FindingStatus
from data_audit.scripts.compare_election_to_source import load_source_by_geoid

# MEDSL party -> source CSV column.
PARTY_TO_SOURCE_COLUMN = {
    "DEMOCRAT": "E_20_PRES_Dem",
    "REPUBLICAN": "E_20_PRES_Rep",
}

# Verified empirically: reassigning Kansas City's separate return to
# Jackson County reconciles Jackson's Dem and Rep deltas to exactly zero.
KANSAS_CITY_PSEUDO_FIPS = "2938000"
JACKSON_COUNTY_MO = "29095"

# DRA block allocation moves single-digit vote counts across county
# lines; 10 votes covers it with headroom while still flagging anything
# that could matter.
ALLOCATION_TOLERANCE_VOTES = 10

MEDSL_NAME = MEDSL_CSV.name


def load_medsl_2020_by_geoid() -> pd.DataFrame:
    """2020 presidential D/R votes per county GEOID, from MEDSL.

    Some states report one TOTAL row per county-party; others split by
    vote mode (and 56 county-parties have both). Where a TOTAL row
    exists it is authoritative and the split rows would double-count,
    so TOTAL wins; otherwise the modes are summed.
    """
    medsl = pd.read_csv(MEDSL_CSV, dtype={"county_fips": "string"})
    votes = medsl[
        (medsl.year == 2020)
        & (medsl.office == "US PRESIDENT")
        & medsl.party.isin(PARTY_TO_SOURCE_COLUMN)
    ].copy()
    votes = votes.dropna(subset=["county_fips"])  # RI's FEDERAL PRECINCT rows
    votes["GEOID"] = votes.county_fips.str.zfill(5)
    votes.loc[votes.GEOID == KANSAS_CITY_PSEUDO_FIPS, "GEOID"] = JACKSON_COUNTY_MO
    votes = votes[votes.state_po != "AK"]

    def county_party_votes(group: pd.DataFrame) -> float:
        if (group["mode"] == "TOTAL").any():
            return group.loc[group["mode"] == "TOTAL", "candidatevotes"].sum()
        return group["candidatevotes"].sum()

    return (
        votes.groupby(["GEOID", "party"])
        .apply(county_party_votes, include_groups=False)
        .unstack()
    )


def compare_to_medsl(
    source: pd.DataFrame, medsl_votes: pd.DataFrame
) -> list[AuditFinding]:
    """One finding per (county, party), covering every non-Alaska source county."""
    findings = []
    source_counties = source.index[~source.index.str.startswith("02")]
    for geoid in source_counties:
        for party, source_column in PARTY_TO_SOURCE_COLUMN.items():
            source_value = source.at[geoid, source_column]
            source_number = None if pd.isna(source_value) else float(source_value)
            in_medsl = geoid in medsl_votes.index
            medsl_number = float(medsl_votes.at[geoid, party]) if in_medsl else None
            delta = ""
            if source_number is not None and medsl_number is not None:
                difference = source_number - medsl_number
                delta = f"{difference:+.0f}"
                if difference == 0:
                    status = FindingStatus.MATCH
                elif abs(difference) <= ALLOCATION_TOLERANCE_VOTES:
                    status = FindingStatus.ALLOCATION_DELTA
                else:
                    status = FindingStatus.NEEDS_REVIEW
            elif source_number is None and not in_medsl:
                status = FindingStatus.BOTH_MISSING  # Puerto Rico
            elif medsl_number is None:
                status = FindingStatus.ROW_ABSENT  # Kalawao, HI
            else:
                status = FindingStatus.NEEDS_REVIEW  # source NaN, MEDSL has votes
            findings.append(
                AuditFinding(
                    table=MEDSL_NAME,
                    website_code=party,
                    raw_column=source_column,
                    geoid=geoid,
                    county="",
                    website_value="" if medsl_number is None else f"{medsl_number:.0f}",
                    raw_value="" if source_number is None else f"{source_number:.0f}",
                    status=status,
                    delta=delta,
                )
            )
    return findings


def main() -> None:
    source = load_source_by_geoid()
    medsl_votes = load_medsl_2020_by_geoid()
    findings = compare_to_medsl(source, medsl_votes)

    with open(MEDSL_FINDINGS_CSV, "w", newline="") as output_findings:
        writer = csv.DictWriter(
            output_findings, fieldnames=[field.name for field in fields(AuditFinding)]
        )
        writer.writeheader()
        writer.writerows(asdict(finding) for finding in findings)

    by_status = Counter(finding.status for finding in findings)
    print(f"{len(findings)} comparisons -> {MEDSL_FINDINGS_CSV.name}")
    print("(Alaska excluded: MEDSL reports election districts, not boroughs)")
    for status, count in sorted(by_status.items()):
        print(f"  {status:16s} {count}")
    reviews = [f for f in findings if f.status is FindingStatus.NEEDS_REVIEW]
    reviews.sort(key=lambda f: abs(float(f.delta)) if f.delta else 0, reverse=True)
    if reviews:
        print(
            f"largest needs_review deltas (source minus MEDSL), top {min(10, len(reviews))}:"
        )
        for finding in reviews[:10]:
            print(
                f"  {finding.geoid} {finding.website_code:10s} "
                f"source={finding.raw_value} medsl={finding.website_value} "
                f"delta={finding.delta}"
            )


if __name__ == "__main__":
    main()
