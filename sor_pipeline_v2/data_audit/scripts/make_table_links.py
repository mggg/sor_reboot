"""Step 1: Generate table_links.csv, the audit's download manifest.

The CSV contains the list of tables to be downloaded for the audit,
including their dataset, table ID, official title, and the URL to
access them on the Census website.
"""

import csv

import requests

from build_dataset.ingest.acs.feats import ACS_FEATURES
from build_dataset.ingest.acs.feats.mobility_feats import PRIOR_SUFFIX
from build_dataset.ingest.declarations.feature_utils import feature_codes
from build_dataset.ingest.dhc.dhc_api import DHC_COLUMN_PREFIX
from build_dataset.ingest.dhc.dhc_feats import DHC_FEATURES
from build_dataset.ingest.pl.feats.hisp_pop_feats import PL_HISP_FEATURES
from build_dataset.ingest.pl.feats.total_pop_feats import PL_FEATURES
from data_audit.config import TABLE_LINKS_CSV, geo_clause

# Website dataset id -> the metadata path its table titles live under.
DATASET_METADATA_PATHS = {
    "DECENNIALPL2020": "2020/dec/pl",
    "DECENNIALDHC2020": "2020/dec/dhc",
    "ACSDT5Y2020": "2020/acs/acs5",
    "ACSDT5Y2015": "2015/acs/acs5",
}


def table_of(code: str) -> str:
    """A census code's table id: B05003I_012E -> B05003I."""
    return code.split("_")[0]


def tables_by_dataset() -> dict[str, list[str]]:
    """Each dataset's tables, derived from the declared features."""
    pl_codes = feature_codes(PL_FEATURES) + feature_codes(PL_HISP_FEATURES)
    dhc_codes = [
        code.removeprefix(DHC_COLUMN_PREFIX) for code in feature_codes(DHC_FEATURES)
    ]
    acs_codes = feature_codes(ACS_FEATURES)
    acs_current = [code for code in acs_codes if not code.endswith(PRIOR_SUFFIX)]
    acs_prior = [
        code.removesuffix(PRIOR_SUFFIX)
        for code in acs_codes
        if code.endswith(PRIOR_SUFFIX)
    ]
    return {
        "DECENNIALPL2020": sorted({table_of(code) for code in pl_codes}),
        "DECENNIALDHC2020": sorted({table_of(code) for code in dhc_codes}),
        "ACSDT5Y2020": sorted({table_of(code) for code in acs_current}),
        "ACSDT5Y2015": sorted({table_of(code) for code in acs_prior}),
    }


def official_titles(metadata_path: str) -> dict[str, str]:
    """Table id -> official title, from the Census groups.json metadata."""
    response = requests.get(
        f"https://api.census.gov/data/{metadata_path}/groups.json", timeout=30
    )
    response.raise_for_status()
    return {group["name"]: group["description"] for group in response.json()["groups"]}


def main() -> None:
    geo = geo_clause()
    rows = []
    for dataset, tables in tables_by_dataset().items():
        titles = official_titles(DATASET_METADATA_PATHS[dataset])
        for table in tables:
            rows.append(
                {
                    "dataset": dataset,
                    "table": table,
                    "title": titles[table],
                    "url": f"https://data.census.gov/table/{dataset}.{table}?g={geo}",
                }
            )

    with open(TABLE_LINKS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "table", "title", "url"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {TABLE_LINKS_CSV}")


if __name__ == "__main__":
    main()
