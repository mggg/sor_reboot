"""Election audit: county_level_2020.csv vs raw.parquet, ALL counties.

The election source is a local file (not fetched), so unlike the census
comparison this one is free to cover the whole county universe, not just
the audit panel. It verifies the pipeline's transit hop -- source CSV ->
ingest -> raw.parquet -- for both vote columns of every county.
"""

import csv
from collections import Counter
from dataclasses import asdict, fields

import pandas as pd

from data_audit.config import (
    ELECTION_FINDINGS_CSV,
    ELECTION_SOURCE_CSV,
    RAW_PARQUET,
)
from data_audit.findings import AuditFinding, FindingStatus, to_number

SOURCE_TO_RAW_COLUMNS = {
    "E_20_PRES_Dem": "E_20_PRES_DEM",
    "E_20_PRES_Rep": "E_20_PRES_REP",
}

SOURCE_NAME = ELECTION_SOURCE_CSV.name  # the findings' "table" label


def load_source_by_geoid() -> pd.DataFrame:
    """The election CSV indexed by 5-char GEOID.

    county_fips is an integer column, so 01001 arrives as 1001 -- zfill
    restores the leading zero. Duplicate FIPS would silently corrupt an
    indexed lookup, so they are an error, not a warning.
    """
    source = pd.read_csv(ELECTION_SOURCE_CSV)
    geoids = source["county_fips"].astype(str).str.zfill(5)
    duplicated = geoids[geoids.duplicated()]
    if not duplicated.empty:
        raise ValueError(f"duplicate county_fips in source: {list(duplicated)}")
    source.index = pd.Index(geoids, name="GEOID")
    return source


def check_same_counties(source: pd.DataFrame, raw: pd.DataFrame) -> None:
    """Both files must cover exactly the same county universe.

    A county on one side only would otherwise just shrink the comparison
    -- silence, where the audit needs an alarm.
    """
    source_only = source.index.difference(raw.index)
    raw_only = raw.index.difference(source.index)
    if len(source_only) or len(raw_only):
        raise ValueError(
            f"county universes differ: {len(source_only)} GEOIDs only in "
            f"{SOURCE_NAME} (first: {list(source_only[:5])}), "
            f"{len(raw_only)} only in raw.parquet (first: {list(raw_only[:5])})"
        )


def compare_all_counties(
    source_df: pd.DataFrame, raw_df: pd.DataFrame
) -> list[AuditFinding]:
    """One finding per (county, vote column): source value vs raw value."""
    findings = []
    for geoid in raw_df.index:
        for source_column, raw_column in SOURCE_TO_RAW_COLUMNS.items():
            source_value = source_df.at[geoid, source_column]
            raw_value = raw_df.at[geoid, raw_column]
            source_number, raw_number = to_number(source_value), to_number(raw_value)
            if source_number is not None and raw_number is not None:
                status = (
                    FindingStatus.MATCH
                    if source_number == raw_number
                    else FindingStatus.MISMATCH
                )
            elif source_number is None and raw_number is None:
                status = FindingStatus.BOTH_MISSING  # the PR municipalities
            else:
                status = FindingStatus.NEEDS_REVIEW  # missing on ONE side only
            findings.append(
                AuditFinding(
                    table=SOURCE_NAME,
                    website_code=source_column,
                    raw_column=raw_column,
                    geoid=geoid,
                    county=str(raw_df.at[geoid, "NAME"]),
                    website_value=str(source_value),
                    raw_value="" if raw_value is None else str(raw_value),
                    status=status,
                )
            )
    return findings


def main() -> None:
    source = load_source_by_geoid()
    raw = pd.read_parquet(RAW_PARQUET).set_index("GEOID")
    check_same_counties(source, raw)

    findings = compare_all_counties(source, raw)

    with open(ELECTION_FINDINGS_CSV, "w", newline="") as output_findings:
        writer = csv.DictWriter(
            output_findings, fieldnames=[field.name for field in fields(AuditFinding)]
        )
        writer.writeheader()
        writer.writerows(asdict(finding) for finding in findings)

    by_status = Counter(finding.status for finding in findings)
    print(f"{len(findings)} comparisons -> {ELECTION_FINDINGS_CSV.name}")
    for status, count in sorted(by_status.items()):
        print(f"  {status:14s} {count}")
    for finding in findings:
        if finding.status in (FindingStatus.MISMATCH, FindingStatus.NEEDS_REVIEW):
            print(
                f"  {finding.status} {finding.geoid} {finding.county} "
                f"{finding.website_code}: source={finding.website_value} "
                f"raw={finding.raw_value}"
            )


if __name__ == "__main__":
    main()
