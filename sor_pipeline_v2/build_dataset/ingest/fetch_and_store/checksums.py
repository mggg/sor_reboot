"""SHA-256 digests of the raw source files, and what each one is actually worth.

Report the current state:
`python -m build_dataset.ingest.fetch_and_store.checksums`

Record the files as they stand now (after an intentional refetch):
`python -m build_dataset.ingest.fetch_and_store.checksums --write`

Drop a record for a source the build no longer uses:
`python -m build_dataset.ingest.fetch_and_store.checksums --forget FILE`
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from build_dataset.ingest.acs.acs_api import (
    ACS5_2015_PRIOR_STEM,
    ACS5_2020_STEM,
)
from build_dataset.ingest.dhc.dhc_api import DHC_STEM
from build_dataset.ingest.election.election_api import (
    MEDSL_COUNTY_RAW_CSV,
    MEDSL_COUNTY_RAW_MD5,
)
from build_dataset.ingest.fetch_and_store.census_client import NATIONAL_COUNTIES
from build_dataset.ingest.fetch_and_store.source_cache import cache_path
from build_dataset.ingest.geometry.geometry_api import COUNTY_GEOMETRY_2020_PARQUET
from build_dataset.ingest.pl.pl_api import (
    PL_2020_HISPANIC_STEM,
    PL_2020_TOTAL_STEM,
)
from utils.config import (
    RAW_NATIONAL_DIR,
    SOURCE_RECORDS_DIR,
    STATE_FIPS_TO_NAME,
)

RAW_CHECKSUM_MANIFEST = SOURCE_RECORDS_DIR / "raw_checksums.json"


class ChecksumOrigin(StrEnum):
    """Where a recorded checksum came from. Either published by the depositor or computed by ourselves."""

    PUBLISHED = "published"
    CUSTOM = "custom_self"


class DigestAlgorithm(StrEnum):
    """The algorithm used to compute a checksum."""

    SHA256 = "sha256"
    MD5 = "md5"


class ChecksumStatus(StrEnum):
    """The outcome of comparing one file against the manifest."""

    MATCH = "match"
    MISMATCH = "MISMATCH"
    ABSENT = "absent"
    UNRECORDED = "unrecorded"


@dataclass(frozen=True)
class PublishedChecksum:
    """A checksum a depositor published, in whatever algorithm they chose."""

    algorithm: DigestAlgorithm
    checksum_value: str
    checksum_source_type: str = ChecksumOrigin.PUBLISHED
    checksum_source_description: str | None = None


@dataclass(frozen=True)
class SelfRecordedChecksum:
    """A checksum we computed and recorded in the manifest."""

    checksum_sha_256_value: str
    checksum_source_type: str = ChecksumOrigin.CUSTOM


@dataclass
class FullChecksumEntry:
    self_recorded_checksum: SelfRecordedChecksum
    published_checksum: PublishedChecksum | None = None


def _county_cache_name(stem: str) -> str:
    """The filename a census source's national-counties cache carries.

    Parameters
    ----------
    stem : str
        The source's cache filename stem.

    Returns
    -------
    str
        The basename inside RAW_NATIONAL_DIR -- the key the manifest uses.
    """
    return cache_path(stem, NATIONAL_COUNTIES).name


RAW_SOURCE_ORIGINS: dict[str, ChecksumOrigin] = {
    _county_cache_name(PL_2020_TOTAL_STEM): ChecksumOrigin.CUSTOM,
    _county_cache_name(PL_2020_HISPANIC_STEM): ChecksumOrigin.CUSTOM,
    _county_cache_name(DHC_STEM): ChecksumOrigin.CUSTOM,
    _county_cache_name(ACS5_2020_STEM): ChecksumOrigin.CUSTOM,
    _county_cache_name(ACS5_2015_PRIOR_STEM): ChecksumOrigin.CUSTOM,
    COUNTY_GEOMETRY_2020_PARQUET: ChecksumOrigin.CUSTOM,
    MEDSL_COUNTY_RAW_CSV: ChecksumOrigin.PUBLISHED,
}

# The raw caches the tract build writes, one file per state. Declared as
# templates rather than names because which ones exist depends on which
# states have been built, and `build_manifest` hard-fails on a declared
# file that is absent -- a CA-only build has to stay recordable.
# Raw files the build fetches one state at a time. Empty since the tract
# election source became the lab's GerryDB release: that release is
# delivered as files rather than fetched, and it is not written to
# RAW_NATIONAL_DIR, which is the only directory this manifest covers.
# The VEST and TIGER archives that used to be declared here are gone
# along with the proration that read them; records already written for
# them stay in the manifest, which is additive, until `--forget` drops
# them by name.
PER_STATE_SOURCE_TEMPLATES: dict[str, ChecksumOrigin] = {}

PUBLISHED_CHECKSUMS: dict[str, PublishedChecksum] = {
    MEDSL_COUNTY_RAW_CSV: PublishedChecksum(
        algorithm=DigestAlgorithm.MD5,
        checksum_value=MEDSL_COUNTY_RAW_MD5,
        checksum_source_type=ChecksumOrigin.PUBLISHED,
        checksum_source_description="Harvard Dataverse metadata API, doi:10.7910/DVN/VOQCHQ",
    ),
}


def declared_sources() -> dict[str, ChecksumOrigin]:
    """Every raw file the manifest covers, in inventory order.

    The national sources always; each per-state cache only when it is on
    disk, so the inventory tracks what has actually been built.

    Returns
    -------
    dict
        Filename in RAW_NATIONAL_DIR -> where its checksum comes from.
    """
    declared = dict(RAW_SOURCE_ORIGINS)
    for template, origin in PER_STATE_SOURCE_TEMPLATES.items():
        for state_fips in sorted(STATE_FIPS_TO_NAME):
            filename = template.format(state_fips=state_fips)
            if (RAW_NATIONAL_DIR / filename).exists():
                declared[filename] = origin
    return declared


def published_checksums() -> dict[str, PublishedChecksum]:
    """Depositor-published digests, by filename.

    Only MEDSL's, pinned in `election_api`. Still a function rather than
    a literal: it was one when VEST archives contributed their published
    digests here, and a per-state source that publishes one can be added
    back without changing the callers.

    Returns
    -------
    dict
        Filename -> the depositor's own checksum, naming the release it
        was published in.
    """
    published = dict(PUBLISHED_CHECKSUMS)
    return published


@dataclass(frozen=True)
class ChecksumFinding:
    """One file's SHA-256 compared against the manifest."""

    filename: str
    status: ChecksumStatus
    origin: ChecksumOrigin
    recorded: str
    actual: str


def file_sha256(path: Path) -> str:
    """The file's SHA-256.

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
    return hashlib.new(DigestAlgorithm.SHA256, path.read_bytes()).hexdigest()


def file_md5(path: Path) -> str:
    """The file's MD5 -- ONLY for comparing against a depositor's published value.

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
    return hashlib.new(DigestAlgorithm.MD5, path.read_bytes()).hexdigest()


def build_manifest() -> dict[str, str | dict[str, FullChecksumEntry | dict]]:
    """Hash every declared raw file and assemble the manifest.

    A PUBLISHED file is additionally verified against the depositor's own
    digest, in the depositor's algorithm, as it is recorded -- so the
    manifest cannot be written from a file that already fails its
    provenance check.

    Additive: an entry recorded earlier for a file no longer on disk is
    carried through unchanged rather than dropped. A per-state cache is
    declared by being PRESENT, so deleting a 10 GB archive to free space
    would otherwise take its SHA-256 out of the record on the next write,
    and the record is the only thing that still says what the dataset was
    built from. `forget_entries` is the one way an entry goes away.

    Returns
    -------
    dict
        `written` (an ISO-8601 local timestamp) and `files`: one entry
        per declared source, carrying the SHA-256 we computed and, for a
        published file, the depositor's own checksum -- plus any earlier
        entry whose file is gone, exactly as it was recorded.

    Raises
    ------
    FileNotFoundError
        If a declared raw file is absent -- run the build first. A file
        that is merely no longer declared is kept, not raised on.
    ValueError
        If a PUBLISHED file's digest differs from the published value.
    """
    file_manifest: dict[str, FullChecksumEntry] = {}
    published_by_filename = published_checksums()
    for filename in declared_sources():
        path = RAW_NATIONAL_DIR / filename
        if not path.exists():
            raise FileNotFoundError(
                f"{filename} is not in {RAW_NATIONAL_DIR}; run the build before "
                "recording checksums."
            )
        # Deliberately not the file's origin: this digest is one we
        # computed, whoever published the file. A PUBLISHED file's own
        # digest goes in `published_checksum` below, and the origin is
        # reported from RAW_SOURCE_ORIGINS at verify time.
        file_entry: FullChecksumEntry = FullChecksumEntry(
            self_recorded_checksum=SelfRecordedChecksum(
                checksum_sha_256_value=file_sha256(path),
            )
        )
        published = published_by_filename.get(filename)
        if published is not None:
            orig_hash = (
                file_md5(path)
                if published.algorithm == DigestAlgorithm.MD5
                else file_sha256(path)
            )
            if orig_hash != published.checksum_value:
                raise ValueError(
                    f"{filename}: {published.algorithm} {orig_hash} does not match the "
                    f"published checksum {published.checksum_value}; the local copy is not "
                    "the released file, so it must not be recorded as provenance."
                )
            file_entry.published_checksum = published
        file_manifest[filename] = file_entry

    carried = {
        filename: entry
        for filename, entry in _recorded_entries().items()
        if filename not in file_manifest
    }
    if carried:
        print(
            f"  carried forward {len(carried)} record(s) for files no longer on "
            f"disk: {', '.join(sorted(carried))}"
        )
    merged: dict[str, FullChecksumEntry | dict] = {**carried, **file_manifest}
    return {
        "written": datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
        "files": merged,
    }


def _recorded_entries() -> dict[str, dict]:
    """The `files` block of the manifest on disk, or {} if none exists yet.

    Returns
    -------
    dict
        Filename -> the entry as it was written, left as read so a
        carried-forward record is byte-identical to what it replaced.
    """
    if not RAW_CHECKSUM_MANIFEST.exists():
        return {}
    return dict(read_manifest()["files"])


def forget_entries(filenames: list[str]) -> Path:
    """Drop records by name, for sources the build no longer uses.

    The counterpart to `build_manifest` never removing anything: an entry
    for a retired source would otherwise be carried forward forever.

    Parameters
    ----------
    filenames : list of str
        Names exactly as the manifest records them.

    Returns
    -------
    Path
        The manifest written.

    Raises
    ------
    FileNotFoundError
        If no manifest has been recorded yet.
    KeyError
        If any name is not in the manifest -- naming all of them, so a
        typo does not silently drop nothing.
    """
    manifest = read_manifest()
    recorded = manifest["files"]
    absent = [filename for filename in filenames if filename not in recorded]
    if absent:
        raise KeyError(f"not in the manifest: {absent}")
    for filename in filenames:
        del recorded[filename]
    RAW_CHECKSUM_MANIFEST.write_text(
        json.dumps(manifest, sort_keys=True, indent=2, default=asdict) + "\n"
    )
    return RAW_CHECKSUM_MANIFEST


def write_manifest() -> Path:
    """Record the raw files as they stand now.

    Returns
    -------
    Path
        The manifest written.

    Raises
    ------
    FileNotFoundError
        If a declared raw file is absent.
    ValueError
        If a PUBLISHED file fails its published-checksum check.
    """
    manifest = build_manifest()
    RAW_CHECKSUM_MANIFEST.write_text(
        json.dumps(manifest, sort_keys=True, indent=2, default=asdict) + "\n"
    )
    return RAW_CHECKSUM_MANIFEST


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


def _recorded_sha256(entry: dict) -> str:
    """The SHA-256 a manifest entry records, or "" if it records none.

    Parameters
    ----------
    entry : dict
        One `files` value as read back from the manifest JSON.

    Returns
    -------
    str
        The recorded digest, or "" when the entry has no self-recorded
        checksum -- a manifest written before this field existed.
    """
    self_recorded = entry.get("self_recorded_checksum") or {}
    return str(self_recorded.get("checksum_sha_256_value", ""))


def verify_manifest() -> list[ChecksumFinding]:
    """Compare every raw file on disk against the manifest's SHA-256s.

    Returns findings rather than raising, because an intentional refetch
    legitimately changes a census cache; the caller decides what a
    mismatch means. `election_api` is what hard-fails the published file.

    Returns
    -------
    list of ChecksumFinding
        One per declared source, in inventory order.

    Raises
    ------
    FileNotFoundError
        If no manifest has been recorded yet.
    """
    recorded_files = read_manifest()["files"]
    declared = declared_sources()
    # The union: a per-state cache is declared by being present, so one
    # that was recorded and then deleted would otherwise drop out of the
    # report rather than show up as ABSENT.
    inventory = {**dict.fromkeys(recorded_files, ChecksumOrigin.CUSTOM), **declared}
    findings: list[ChecksumFinding] = []
    for filename, origin in inventory.items():
        path = RAW_NATIONAL_DIR / filename
        entry = recorded_files.get(filename, {})
        if not entry:
            findings.append(
                ChecksumFinding(
                    filename,
                    ChecksumStatus.UNRECORDED,
                    origin,
                    "",
                    file_sha256(path) if path.exists() else "",
                )
            )
            continue
        recorded = _recorded_sha256(entry)
        if not path.exists():
            findings.append(
                ChecksumFinding(filename, ChecksumStatus.ABSENT, origin, recorded, "")
            )
            continue
        actual = file_sha256(path)
        status = ChecksumStatus.MATCH if actual == recorded else ChecksumStatus.MISMATCH
        findings.append(ChecksumFinding(filename, status, origin, recorded, actual))
    return findings


def print_findings(findings: list[ChecksumFinding], written: str) -> None:
    """Print one line per file, then a status tally."""
    print(f"manifest recorded {written} ({DigestAlgorithm.SHA256})\n")
    width = max(len(finding.filename) for finding in findings)
    for finding in findings:
        line = f"  {finding.filename:<{width}}  {finding.origin:<9}  {finding.status}"
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
            "column the cache lacked (the api refetches and overwrites). Confirm "
            "that is what happened, then re-record with --write."
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m build_dataset.ingest.fetch_and_store.checksums",
        description="SHA-256s of the raw source files: report drift, or re-record.",
    )
    # Mutually exclusive, and verifying stays the default: forgetting a
    # flag must never overwrite the manifest you were checking against.
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--verify",
        action="store_true",
        help="compare the raw files against the manifest (the default)",
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
        metavar="FILE",
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
