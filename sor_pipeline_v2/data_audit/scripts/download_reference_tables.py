"""Step 2: download every source table from data.census.gov.

This draws from the previous step (make_table_links.py) and builds the dataset from a different endpoint,
not the api.census.gov one the pipeline uses.

Each table lands in reference_tables/<DATASET>.<TABLE>/ with all seven audit
counties as rows of its Data.csv, ready to examine by hand.
"""

import csv
import io
import time
import zipfile

import requests

from data_audit.config import (
    REFERENCE_TABLES_DIR,
    TABLE_LINKS_CSV,
    geo_clause,
)

DOWNLOAD_ENDPOINT = "https://data.census.gov/api/access/table/download"

GEO = geo_clause()


def download_table_zip(table_id: str) -> bytes:
    """Download one table's zip, exactly as the website's download button builds it."""
    created = requests.post(
        DOWNLOAD_ENDPOINT,
        json={"request": {"id": table_id, "g": GEO}},
        timeout=30,
    )
    created.raise_for_status()
    download_id = created.json()["response"]["download_id"]

    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        time.sleep(3)
        resp = requests.get(
            DOWNLOAD_ENDPOINT, params={"download_id": download_id}, timeout=60
        )
        resp.raise_for_status()
        if resp.headers.get("Content-Type", "").startswith("application/zip"):
            return resp.content
        status = resp.json()["response"]
        if status.get("status") == "error":
            raise RuntimeError(f"{table_id}: download job failed: {status}")
    raise TimeoutError(f"{table_id}: zip not ready after 120s")


def main() -> None:
    with open(TABLE_LINKS_CSV, newline="") as table_links_csv:
        tables = [
            f"{row['dataset']}.{row['table']}"
            for row in csv.DictReader(table_links_csv)
        ]

    REFERENCE_TABLES_DIR.mkdir(exist_ok=True)
    for idx, table_id in enumerate(tables, 1):
        target = REFERENCE_TABLES_DIR / table_id
        if (target / f"{table_id}-Data.csv").exists():
            print(f"[{idx:2d}/{len(tables)}] {table_id}: already downloaded, skipping")
            continue
        blob = download_table_zip(table_id)
        target.mkdir(exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            zf.extractall(target)
        print(
            f"[{idx:2d}/{len(tables)}] {table_id}: {sorted(p.name for p in target.iterdir())}"
        )
        time.sleep(1)


if __name__ == "__main__":
    main()
