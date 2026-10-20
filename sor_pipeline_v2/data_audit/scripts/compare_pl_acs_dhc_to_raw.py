"""Step 3: Compare the website's CSV tables to raw.parquet for the audit counties.

Outcome statuses:
  match           both sides parse as numbers and are equal
  MISMATCH        both sides parse as numbers and differ  <- the alarms
  both_missing    website shows no value and raw holds NaN
  suppression_match  the website shows a suppression mark and raw holds
                  exactly the sentinel the Census documents for it (see
                  KNOWN_SUPPRESSION_PAIRS) -- the same fact in each
                  channel's dialect, verified automatically
  needs_review    no automated verdict: a non-numeric pair the script has
                  no rule for (an undocumented mark, a jumbo value like
                  '250,000+'), shown verbatim for a human to judge
  row_absent      the county has no row in the website table; raw's value
                  shown (expected: the known suppression/PR stories)
"""

import csv
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, fields
from pathlib import Path

import pandas as pd

from data_audit.config import (
    COMPARISON_FINDINGS_CSV,
    COUNTIES_TO_AUDIT,
    RAW_PARQUET,
    REFERENCE_TABLES_DIR,
)
from data_audit.findings import AuditFinding, FindingStatus, to_number

# Website marks that mean "no value here":
WEBSITE_MISSING_MARKS = {"", "-", "(X)", "N", "null", "*", "**", "***", "*****"}

# Website suppression mark -> the sentinel the Census API delivers for the
# same fact (documented ACS conventions; both mean the value is withheld).
KNOWN_SUPPRESSION_PAIRS: dict[str, float] = {
    "*****": -555555555,  # MOE: estimate is controlled
    "-": -666666666,  # estimate cannot be computed
    "**": -222222222,  # MOE cannot be computed
}


def raw_column_for(dataset_name: str, code: str) -> str:
    """Return the raw.parquet column name corresponding to the website code."""
    if dataset_name.startswith("DECENNIALDHC"):
        return f"DHC_{code}"
    if dataset_name == "ACSDT5Y2015":
        return f"{code}_PRIOR"
    return code


def compare_table(
    table_dir: Path, raw_counties_to_audit: pd.DataFrame
) -> list[AuditFinding]:
    """Compare a website table against raw data for the audit counties."""
    dataset_name = table_dir.name.split(".")[0]
    data_csv = next(table_dir.glob("*-Data.csv"))
    with open(data_csv, newline="", encoding="utf-8-sig") as input_csv:
        reader = csv.DictReader(input_csv)
        if reader.fieldnames is None:
            raise ValueError(f"{data_csv} is empty -- no header row")
        website_codes = reader.fieldnames
        website_county_rows = list(reader)[
            1:
        ]  # skip the first row, which contains English labels, not county data

    website_code_to_raw_column = {
        code: raw_column_for(dataset_name, code)
        for code in website_codes
        if code != "NAME"
        and raw_column_for(dataset_name, code) in raw_counties_to_audit.columns
    }

    website_geoids = {row["GEO_ID"][-5:] for row in website_county_rows}
    missing_website_geoids = raw_counties_to_audit.index.difference(
        list(website_geoids)
    )
    audit_results = published_row_findings(
        table_dir.name,
        website_county_rows,
        website_code_to_raw_column,
        raw_counties_to_audit,
    ) + absent_row_findings(
        table_dir.name,
        missing_website_geoids,
        website_code_to_raw_column,
        raw_counties_to_audit,
    )
    return audit_results


def published_row_findings(
    table_name: str,
    website_county_rows: list[dict[str, str]],
    website_code_to_raw_column: dict[str, str],
    raw_counties_to_audit: pd.DataFrame,
) -> list[AuditFinding]:
    """Compare every county row the website table published against raw."""
    findings = []
    for row in website_county_rows:
        geoid = row["GEO_ID"][-5:]  # "0500000US12086" -> "12086"
        for website_code, raw_column in website_code_to_raw_column.items():
            website_value = row[website_code]
            raw_value = raw_counties_to_audit.at[geoid, raw_column]
            website_number, raw_number = to_number(website_value), to_number(raw_value)
            if website_number is not None and raw_number is not None:
                status = (
                    FindingStatus.MATCH
                    if website_number == raw_number
                    else FindingStatus.MISMATCH
                )
            elif (
                website_value.strip() in KNOWN_SUPPRESSION_PAIRS
                and raw_number == KNOWN_SUPPRESSION_PAIRS[website_value.strip()]
            ):
                status = FindingStatus.SUPPRESSION_MATCH
            elif website_value.strip() in WEBSITE_MISSING_MARKS and raw_number is None:
                status = FindingStatus.BOTH_MISSING
            else:
                status = FindingStatus.NEEDS_REVIEW
            findings.append(
                AuditFinding(
                    table=table_name,
                    website_code=website_code,
                    raw_column=raw_column,
                    geoid=geoid,
                    county=row["NAME"],
                    website_value=website_value,
                    raw_value="" if raw_value is None else str(raw_value),
                    status=status,
                )
            )
    return findings


def absent_row_findings(
    table_name: str,
    missing_geoids: Iterable[str],
    website_code_to_raw_column: dict[str, str],
    raw_counties_to_audit: pd.DataFrame,
) -> list[AuditFinding]:
    """Account for panel counties the website table did NOT publish.

    Raw's value travels with each finding: for a legitimately unpublished
    row it should be NaN, and a number here is as alarming as a MISMATCH.
    """
    findings = []
    for missing_geoid in missing_geoids:
        for website_code, raw_column in website_code_to_raw_column.items():
            raw_value = raw_counties_to_audit.at[missing_geoid, raw_column]
            findings.append(
                AuditFinding(
                    table=table_name,
                    website_code=website_code,
                    raw_column=raw_column,
                    geoid=missing_geoid,
                    county=COUNTIES_TO_AUDIT[missing_geoid],
                    website_value="<row absent>",
                    raw_value="" if raw_value is None else str(raw_value),
                    status=FindingStatus.ROW_ABSENT,
                )
            )
    return findings


def main() -> None:
    raw_df = pd.read_parquet(RAW_PARQUET).set_index("GEOID")
    raw_counties_to_audit = raw_df.loc[list(COUNTIES_TO_AUDIT)]

    audit_findings = []
    for table_dir in sorted(REFERENCE_TABLES_DIR.iterdir()):
        if table_dir.is_dir():
            audit_findings.extend(compare_table(table_dir, raw_counties_to_audit))

    with open(COMPARISON_FINDINGS_CSV, "w", newline="") as output_findings:
        writer = csv.DictWriter(
            output_findings, fieldnames=[field.name for field in fields(AuditFinding)]
        )
        writer.writeheader()
        writer.writerows(asdict(finding) for finding in audit_findings)

    by_status = Counter(finding.status for finding in audit_findings)
    print(f"{len(audit_findings)} comparisons -> {COMPARISON_FINDINGS_CSV.name}")
    for status, count in sorted(by_status.items()):
        print(f"  {status:14s} {count}")
    for finding in audit_findings:
        if finding.status is FindingStatus.MISMATCH:
            print(
                f"  MISMATCH {finding.table} {finding.website_code} "
                f"{finding.geoid}: website={finding.website_value} "
                f"raw={finding.raw_value}"
            )


if __name__ == "__main__":
    main()
