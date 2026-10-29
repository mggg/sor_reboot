"""SHA-256 digests of every source file the county and tract builds read.

Report the current state:
`python -m build_dataset.ingest.fetch_and_store.checksums`

Record the files as they stand now (after an intentional refetch):
`python -m build_dataset.ingest.fetch_and_store.checksums --write`

Drop a record for a source the build no longer uses:
`python -m build_dataset.ingest.fetch_and_store.checksums --forget FILE`

The inputs live in two directories under DATA_DIR -- the raw caches the
build writes (RAW_NATIONAL_DIR) and the GerryDB release it only reads
(GERRYDB_RELEASE_DIR) -- so every record is keyed by its path relative
to DATA_DIR, e.g. `national/raw/dhc_national_counties.csv` or
`RELEASE_geopackages/ri_districtr_tract_view_v2.gpkg`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import get_args

from build_dataset.ingest.acs.acs_api import (
    ACS5_2015_PRIOR_STEM,
    ACS5_2020_STEM,
)
from build_dataset.ingest.dhc.dhc_api import DHC_STEM
from build_dataset.ingest.election.election_api import (
    GERRYDB_VIEW_TEMPLATE,
    GerryDBLevel,
)
from build_dataset.ingest.fetch_and_store.census_client import (
    NATIONAL_COUNTIES,
    state_tracts,
)
from build_dataset.ingest.fetch_and_store.source_cache import cache_path
from build_dataset.ingest.geometry.geometry_api import (
    COUNTY_GEOMETRY_2020_PARQUET,
    TRACT_GEOMETRY_2020_PARQUET_TEMPLATE,
)
from build_dataset.ingest.pl.pl_api import (
    PL_2020_HISPANIC_STEM,
    PL_2020_TOTAL_STEM,
)
from utils.config import (
    DATA_DIR,
    GERRYDB_RELEASE_DIR,
    RAW_NATIONAL_DIR,
    SOURCE_RECORDS_DIR,
    STATE_FIPS_TO_USPS,
)

RAW_CHECKSUM_MANIFEST = SOURCE_RECORDS_DIR / "raw_checksums.json"
DIGEST_ALGORITHM = "sha256"

# The census sources fetched through the API, one cache per scope.
CENSUS_CACHE_STEMS: tuple[str, ...] = (
    PL_2020_TOTAL_STEM,
    PL_2020_HISPANIC_STEM,
    DHC_STEM,
    ACS5_2020_STEM,
    ACS5_2015_PRIOR_STEM,
)


class ChecksumStatus(StrEnum):
    """The outcome of comparing one file against the manifest."""

    MATCH = "match"
    MISMATCH = "MISMATCH"
    ABSENT = "absent"
    UNRECORDED = "unrecorded"


@dataclass(frozen=True)
class ChecksumFinding:
    """One file's SHA-256 compared against the manifest."""

    key: str
    status: ChecksumStatus
    recorded: str
    actual: str


def manifest_key(path: Path) -> str:
    """The name a file is recorded under: its path relative to DATA_DIR.

    Parameters
    ----------
    path : Path
        A file inside DATA_DIR.

    Returns
    -------
    str
        The relative path, with forward slashes on every platform.

    Raises
    ------
    ValueError
        If `path` is not inside DATA_DIR.
    """
    return path.relative_to(DATA_DIR).as_posix()


def national_sources() -> list[Path]:
    """The county build's single-file inputs, which must all be present.

    Returns
    -------
    list of Path
        The five national census caches and the county geometry.
    """
    return [
        *(cache_path(stem, NATIONAL_COUNTIES) for stem in CENSUS_CACHE_STEMS),
        RAW_NATIONAL_DIR / COUNTY_GEOMETRY_2020_PARQUET,
    ]


def per_state_sources(state_fips: str) -> list[Path]:
    """Every file either build reads for one state.

    The tract build's census caches and tract geometry, plus the
    state's GerryDB views at both levels -- the county build reads the
    county view, the tract build the tract view.

    Parameters
    ----------
    state_fips : str
        Two-digit state FIPS code.

    Returns
    -------
    list of Path
        Where each of the state's input files would be; whether it
        exists is the caller's question.
    """
    scope = state_tracts(state_fips)
    usps = STATE_FIPS_TO_USPS[state_fips].lower()
    return [
        *(cache_path(stem, scope) for stem in CENSUS_CACHE_STEMS),
        RAW_NATIONAL_DIR
        / TRACT_GEOMETRY_2020_PARQUET_TEMPLATE.format(state_fips=state_fips),
        *(
            GERRYDB_RELEASE_DIR / GERRYDB_VIEW_TEMPLATE.format(usps=usps, level=level)
            for level in get_args(GerryDBLevel)
        ),
    ]


def declared_sources() -> list[Path]:
    """Every source file the manifest covers, in inventory order.

    The national sources always; each per-state file only when it is on
    disk, so the inventory tracks what has actually been built (a
    CA-only tract build has to stay recordable) and DC and Puerto Rico,
    which have no GerryDB views, simply contribute none.

    Returns
    -------
    list of Path
        The national sources, then each state's present files.
    """
    declared = national_sources()
    for state_fips in sorted(STATE_FIPS_TO_USPS):
        declared.extend(path for path in per_state_sources(state_fips) if path.exists())
    return declared


def file_sha256(path: Path) -> str:
    """The file's SHA-256, read in chunks so a large file is never held whole.

    Parameters
    ----------
    path : Path
        The file to hash.

    Returns
    -------
    str
        Lowercase hex digest.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, DIGEST_ALGORITHM).hexdigest()


def build_manifest() -> dict:
    """Hash every declared source file and assemble the manifest.

    Additive: an entry recorded earlier for a file no longer on disk is
    carried through unchanged rather than dropped. A per-state file is
    declared by being PRESENT, so deleting one to free space would
    otherwise take its SHA-256 out of the record on the next write, and
    the record is the only thing that still says what the dataset was
    built from. `forget_entries` is the one way an entry goes away.

    Returns
    -------
    dict
        `written` (an ISO-8601 local timestamp), `algorithm`, and
        `files`: the key of each declared source -> its SHA-256, plus any
        earlier entry whose file is gone, exactly as it was recorded.

    Raises
    ------
    FileNotFoundError
        If a national source is absent -- run the county build first. A
        file that is merely no longer declared is kept, not raised on.
    """
    files: dict[str, dict[str, str]] = {}
    for path in declared_sources():
        if not path.exists():
            raise FileNotFoundError(
                f"{manifest_key(path)} is not on disk; run the county build "
                "before recording checksums."
            )
        files[manifest_key(path)] = {DIGEST_ALGORITHM: file_sha256(path)}

    carried = {
        key: entry for key, entry in _recorded_entries().items() if key not in files
    }
    if carried:
        print(
            f"  carried forward {len(carried)} record(s) for files no longer on "
            f"disk: {', '.join(sorted(carried))}"
        )
    return {
        "written": datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
        "algorithm": DIGEST_ALGORITHM,
        "files": {**carried, **files},
    }


def _recorded_entries() -> dict[str, dict]:
    """The `files` block of the manifest on disk, or {} if none exists yet.

    Returns
    -------
    dict
        Key -> the entry as it was written, left as read so a
        carried-forward record is byte-identical to what it replaced.
    """
    if not RAW_CHECKSUM_MANIFEST.exists():
        return {}
    return dict(read_manifest()["files"])


def _write(manifest: dict) -> Path:
    """Write the manifest in its canonical form.

    Parameters
    ----------
    manifest : dict
        As `build_manifest` returns.

    Returns
    -------
    Path
        The manifest written.
    """
    RAW_CHECKSUM_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    RAW_CHECKSUM_MANIFEST.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    )
    return RAW_CHECKSUM_MANIFEST


def forget_entries(keys: list[str]) -> Path:
    """Drop records by key, for sources the build no longer uses.

    The counterpart to `build_manifest` never removing anything: an entry
    for a retired source would otherwise be carried forward forever.

    Parameters
    ----------
    keys : list of str
        Keys exactly as the manifest records them.

    Returns
    -------
    Path
        The manifest written.

    Raises
    ------
    FileNotFoundError
        If no manifest has been recorded yet.
    KeyError
        If any key is not in the manifest -- naming all of them, so a
        typo does not silently drop nothing.
    """
    manifest = read_manifest()
    recorded = manifest["files"]
    absent = [key for key in keys if key not in recorded]
    if absent:
        raise KeyError(f"not in the manifest: {absent}")
    for key in keys:
        del recorded[key]
    return _write(manifest)


def write_manifest() -> Path:
    """Record the source files as they stand now.

    Returns
    -------
    Path
        The manifest written.

    Raises
    ------
    FileNotFoundError
        If a national source is absent.
    """
    return _write(build_manifest())


def read_manifest() -> dict:
    """The recorded manifest.

    Returns
    -------
    dict
        As `build_manifest` returns.

    Raises
    ------
    FileNotFoundError
        If no manifest has been recorded yet.
    """
    if not RAW_CHECKSUM_MANIFEST.exists():
        raise FileNotFoundError(
            f"no checksum manifest at {RAW_CHECKSUM_MANIFEST}; record one with "
            "`--write`."
        )
    return json.loads(RAW_CHECKSUM_MANIFEST.read_text())


def verify_manifest() -> list[ChecksumFinding]:
    """Compare every source file on disk against the manifest's SHA-256s.

    Returns findings rather than raising, because an intentional refetch
    legitimately changes a census cache; the caller decides what a
    mismatch means.

    Returns
    -------
    list of ChecksumFinding
        One per recorded or declared file, recorded ones first.

    Raises
    ------
    FileNotFoundError
        If no manifest has been recorded yet.
    """
    recorded_files = read_manifest()["files"]
    # The union: a per-state file is declared by being present, so one
    # that was recorded and then deleted would otherwise drop out of the
    # report rather than show up as ABSENT.
    inventory = [
        *recorded_files,
        *(
            key
            for key in map(manifest_key, declared_sources())
            if key not in recorded_files
        ),
    ]
    findings: list[ChecksumFinding] = []
    for key in inventory:
        path = DATA_DIR / key
        recorded = str(recorded_files.get(key, {}).get(DIGEST_ALGORITHM, ""))
        if not recorded:
            actual = file_sha256(path) if path.exists() else ""
            findings.append(ChecksumFinding(key, ChecksumStatus.UNRECORDED, "", actual))
        elif not path.exists():
            findings.append(ChecksumFinding(key, ChecksumStatus.ABSENT, recorded, ""))
        else:
            actual = file_sha256(path)
            status = (
                ChecksumStatus.MATCH if actual == recorded else ChecksumStatus.MISMATCH
            )
            findings.append(ChecksumFinding(key, status, recorded, actual))
    return findings


def print_findings(findings: list[ChecksumFinding], written: str) -> None:
    """Print one line per file that is not a match, then a status tally.

    Matches are only counted: with several hundred per-state files, a
    line for each would bury the ones that need attention.
    """
    print(f"manifest recorded {written} ({DIGEST_ALGORITHM})\n")
    for finding in findings:
        if finding.status is ChecksumStatus.MATCH:
            continue
        line = f"  {finding.status:<10}  {finding.key}"
        if finding.status is ChecksumStatus.MISMATCH:
            line += (
                f"\n      recorded {finding.recorded}\n      actual   {finding.actual}"
            )
        print(line)

    tally: dict[str, int] = {}
    for finding in findings:
        tally[str(finding.status)] = tally.get(str(finding.status), 0) + 1
    print("\n" + ", ".join(f"{count} {status}" for status, count in tally.items()))
    if tally.get(str(ChecksumStatus.MISMATCH)):
        print(
            "\nA census cache mismatch is expected after declaring a feature whose "
            "column the cache lacked (the api refetches and overwrites). A GerryDB "
            "view mismatch means the release file itself was replaced. Confirm "
            "that is what happened, then re-record with --write."
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m build_dataset.ingest.fetch_and_store.checksums",
        description="SHA-256s of the source files: report drift, or re-record.",
    )
    # Mutually exclusive, and verifying stays the default: forgetting a
    # flag must never overwrite the manifest you were checking against.
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--verify",
        action="store_true",
        help="compare the source files against the manifest (the default)",
    )
    action.add_argument(
        "--write",
        action="store_true",
        help="record the files as they stand now; updates every file present "
        "and keeps the records of any that are gone",
    )
    action.add_argument(
        "--forget",
        nargs="+",
        default=None,
        metavar="KEY",
        help="drop these records, for a source the build no longer uses. "
        "--write never removes one, so this is the only way an entry goes away.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.write:
        print(f"recorded -> {write_manifest()}")
    elif args.forget:
        print(f"forgot {', '.join(args.forget)} -> {forget_entries(args.forget)}")
    else:
        print_findings(verify_manifest(), read_manifest()["written"])
