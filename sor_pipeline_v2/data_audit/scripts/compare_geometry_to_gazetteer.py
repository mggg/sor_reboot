"""Geometry audit: raw.parquet's TIGER columns vs the Census Gazetteer file.

The pipeline reads ALAND / INTPTLAT / INTPTLON from the TIGER/Line
shapefile at runtime; the Gazetteer is the Census's published flat-file
listing of the same quantities. Comparing the two checks the pipeline's
transit hop AND cross-checks two Census products against each other --
it cannot detect an error in the underlying geography database both
products share.

Covers all counties in raw.parquet. (Observed: the 2020 county Gazetteer
holds exactly the pipeline's 3221-county universe. Gazetteer-only
geographies would be counted and ignored; a raw county MISSING from the
Gazetteer is an error.)

ALAND must match exactly (integer square meters). Coordinates are
compared within COORD_TOLERANCE_DEGREES, since the two products round
independently; each finding records both values verbatim either way.

Run from sor_pipeline_v2:
  uv run python -m feature_audit.scripts.compare_geometry_to_gazetteer
"""

import csv
import io
import zipfile
from collections import Counter
from dataclasses import asdict, fields

import pandas as pd
import requests

from data_audit.config import (
    GAZETTEER_TXT,
    GAZETTEER_URL,
    GEOMETRY_FINDINGS_CSV,
    RAW_PARQUET,
)
from data_audit.findings import AuditFinding, FindingStatus, to_number

RAW_TO_GAZETTEER_COLUMNS = {
    "ALAND": "ALAND",
    "INTPTLAT": "INTPTLAT",
    "INTPTLON": "INTPTLONG",
}

# ~0.1 meter. The two products publish the same internal point but round
# independently in the last decimal place.
COORD_TOLERANCE_DEGREES = 1e-6

COORDINATE_COLUMNS = {"INTPTLAT", "INTPTLON"}


def load_gazetteer_by_geoid() -> pd.DataFrame:
    """The Gazetteer counties table, downloading and caching it on first run."""
    if not GAZETTEER_TXT.exists():
        response = requests.get(GAZETTEER_URL, timeout=60)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            member = archive.namelist()[0]
            GAZETTEER_TXT.write_bytes(archive.read(member))
        print(f"downloaded {GAZETTEER_URL} -> {GAZETTEER_TXT.name}")
    gazetteer = pd.read_csv(GAZETTEER_TXT, sep="\t", dtype={"GEOID": str})
    gazetteer.columns = [column.strip() for column in gazetteer.columns]
    return gazetteer.set_index("GEOID")


def compare_geometry(
    raw_df: pd.DataFrame, gazetteer: pd.DataFrame
) -> list[AuditFinding]:
    """One finding per (county, geometry column): raw vs Gazetteer."""
    missing_from_gazetteer = raw_df.index.difference(gazetteer.index)
    if len(missing_from_gazetteer):
        raise ValueError(
            f"{len(missing_from_gazetteer)} raw counties absent from the "
            f"Gazetteer, first: {list(missing_from_gazetteer[:5])}"
        )

    findings = []
    for geoid in raw_df.index:
        for raw_column, gazetteer_column in RAW_TO_GAZETTEER_COLUMNS.items():
            raw_value = raw_df.at[geoid, raw_column]
            gazetteer_value = gazetteer.at[geoid, gazetteer_column]
            raw_number = to_number(raw_value)
            gazetteer_number = to_number(gazetteer_value)
            if raw_number is None or gazetteer_number is None:
                status = FindingStatus.NEEDS_REVIEW
            elif raw_column in COORDINATE_COLUMNS:
                delta = abs(raw_number - gazetteer_number)
                status = (
                    FindingStatus.MATCH
                    if delta <= COORD_TOLERANCE_DEGREES
                    else FindingStatus.MISMATCH
                )
            else:
                status = (
                    FindingStatus.MATCH
                    if raw_number == gazetteer_number
                    else FindingStatus.MISMATCH
                )
            findings.append(
                AuditFinding(
                    table=GAZETTEER_TXT.name,
                    website_code=gazetteer_column,
                    raw_column=raw_column,
                    geoid=geoid,
                    county=str(raw_df.at[geoid, "NAME"]),
                    website_value=str(gazetteer_value),
                    raw_value="" if raw_value is None else str(raw_value),
                    status=status,
                )
            )
    return findings


def main() -> None:
    raw = pd.read_parquet(RAW_PARQUET).set_index("GEOID")
    gazetteer = load_gazetteer_by_geoid()
    extras = gazetteer.index.difference(raw.index)
    print(
        f"gazetteer lists {len(extras)} geographies outside the pipeline "
        f"universe -- ignored"
    )

    findings = compare_geometry(raw, gazetteer)

    with open(GEOMETRY_FINDINGS_CSV, "w", newline="") as output_findings:
        writer = csv.DictWriter(
            output_findings, fieldnames=[field.name for field in fields(AuditFinding)]
        )
        writer.writeheader()
        writer.writerows(asdict(finding) for finding in findings)

    by_status = Counter(finding.status for finding in findings)
    print(f"{len(findings)} comparisons -> {GEOMETRY_FINDINGS_CSV.name}")
    for status, count in sorted(by_status.items()):
        print(f"  {status:14s} {count}")
    for finding in findings:
        if finding.status is not FindingStatus.MATCH:
            print(
                f"  {finding.status} {finding.geoid} {finding.county} "
                f"{finding.raw_column}: gazetteer={finding.website_value} "
                f"raw={finding.raw_value}"
            )


if __name__ == "__main__":
    main()
