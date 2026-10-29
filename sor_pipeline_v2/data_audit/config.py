"""The audit's shared configuration, each fact spelled once.

The county panel (audit.md records why each pick) and the paths every
script reads or writes. Layout: scripts/ holds the code, data/ holds every
generated artifact -- the manifest, the downloaded website tables, and the
comparison findings.
"""

from pathlib import Path

FEATURE_AUDIT_DIR = Path(__file__).parent
AUDIT_DATA_DIR = FEATURE_AUDIT_DIR / "data"

TABLE_LINKS_CSV = AUDIT_DATA_DIR / "table_links.csv"
REFERENCE_TABLES_DIR = AUDIT_DATA_DIR / "reference_tables"
COMPARISON_FINDINGS_CSV = AUDIT_DATA_DIR / "comparison_findings.csv"
ELECTION_FINDINGS_CSV = AUDIT_DATA_DIR / "election_findings.csv"
GEOMETRY_FINDINGS_CSV = AUDIT_DATA_DIR / "geometry_findings.csv"

# The Census Gazetteer counties file: the published reference for land
# area and internal-point coordinates, independent of the TIGER/Line
# shapefile the pipeline reads (same agency, different product).
GAZETTEER_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_counties_national.zip"
GAZETTEER_TXT = AUDIT_DATA_DIR / "2020_Gaz_counties_national.txt"

# The pipeline's ingest output under audit. Spelled here rather than
# imported from utils.config: the audit scripts stay import-independent of
# the code they check.
RAW_PARQUET = (
    FEATURE_AUDIT_DIR.parent / "data" / "national" / "counties" / "raw.parquet"
)
# The hand-provided election source file the pipeline ingests (DRA2020
# county aggregates -- see the audit report for the provenance chain).
ELECTION_SOURCE_CSV = (
    FEATURE_AUDIT_DIR.parent.parent / "data" / "raw" / "county_level_2020.csv"
)


COUNTIES_TO_AUDIT: dict[str, str] = {
    "12086": "Miami-Dade County, FL",
    "48427": "Starr County, TX",
    "36061": "New York County, NY",
    "48301": "Loving County, TX",
    "72127": "San Juan Municipio, PR",
    "31005": "Arthur County, NE",
    "46102": "Oglala Lakota County, SD",
}


def geo_clause() -> str:
    """The whole panel as one data.census.gov geography clause.

    050XX00US is the Census summary-level prefix for counties; the website
    backend takes multiple geographies colon-separated.
    """
    return ":".join(f"050XX00US{geoid}" for geoid in COUNTIES_TO_AUDIT)
