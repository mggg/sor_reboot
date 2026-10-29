"""What a run was: its code, data, settings, sample, features and machine.

Every run directory gets `metadata_<run name>.json`, written when the run
starts and completed when it ends, so a result traces to the exact commit,
input files and feature definitions behind it -- and a crashed run still
records what it was attempting.

The code is pinned by its commit, which only means something if the
working tree matched it: `warn_if_uncommitted` lists any changes and asks
before running on them, and the metadata records them either way.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

from build_dataset.ingest.declarations.feature_utils import ModelVariable
from build_dataset.model_groups import MODEL_GROUPS
from regression.shared.run_config import run_file
from utils import config

PIPELINE_DIR = Path(__file__).resolve().parents[2]  # sor_pipeline_v2/
# The record `build_dataset.ingest.fetch_and_store.checksums` writes. Not
# imported from there: that module loads the Census API client, which
# refuses to import without CENSUS_API_KEY, and a run that only reads
# finished parquets (as on the cluster) has no key.
RAW_CHECKSUM_MANIFEST = config.SOURCE_RECORDS_DIR / "raw_checksums.json"
# What the run's code is: the pipeline, plus the environment files that
# live one level up at the repo root.
CODE_PATHS = [".", "../pyproject.toml", "../uv.lock"]
# Where a run happened and how many threads it was allowed.
ENVIRONMENT_VARIABLES = [
    "SLURM_JOB_ID",
    "SLURM_JOB_NAME",
    "SLURM_JOB_NODELIST",
    "SLURM_CPUS_PER_TASK",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "LOKY_MAX_CPU_COUNT",
]
SHOWN_CHANGES = 20


def git_state() -> dict[str, Any]:
    """The commit checked out and any uncommitted changes to the code.

    Returns
    -------
    dict
        "commit" (None outside a git checkout) and "uncommitted_changes",
        one `git status --porcelain` line per changed or untracked file.
    """
    try:
        commit = _git("rev-parse", "HEAD")
        changes = _git("status", "--porcelain", "--", *CODE_PATHS).splitlines()
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "uncommitted_changes": []}
    return {"commit": commit, "uncommitted_changes": changes}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=PIPELINE_DIR, capture_output=True, text=True, check=True
    ).stdout.strip()


def warn_if_uncommitted(git: dict[str, Any]) -> None:
    """Warn about uncommitted changes and ask whether to run on them anyway.

    Without a terminal to answer from (a Slurm job), the run continues;
    the changes are in its metadata.

    Raises
    ------
    SystemExit
        If the answer is anything but y.
    """
    changes = git["uncommitted_changes"]
    if not changes:
        return
    commit = (git["commit"] or "no commit")[:8]
    print(
        f"WARNING: {len(changes)} uncommitted change(s), so this run's code "
        f"is not exactly commit {commit}:"
    )
    for line in changes[:SHOWN_CHANGES]:
        print(f"  {line}")
    if len(changes) > SHOWN_CHANGES:
        print(f"  ... and {len(changes) - SHOWN_CHANGES} more")
    if not sys.stdin.isatty():
        print("no terminal to answer from: continuing; the changes go in the metadata")
        return
    if input("run anyway? [y/N] ").strip().lower() != "y":
        raise SystemExit("stopped: commit the changes, or answer y to run on them")


def file_sha256(path: Path) -> str:
    """The file's SHA-256, as the checksum manifest records it."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _shown_path(path: Path) -> str:
    """The path relative to DATA_DIR where it can be, so records match across machines."""
    try:
        return str(path.resolve().relative_to(config.DATA_DIR.resolve()))
    except ValueError:
        return str(path)


def describe_input(path: Path) -> dict[str, Any]:
    """An input file's path (relative to DATA_DIR where it can be), size and SHA-256."""
    return {
        "path": _shown_path(path),
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
        "modified": datetime.fromtimestamp(path.stat().st_mtime, UTC)
        .astimezone()
        .isoformat(timespec="seconds"),
    }


def describe_sample(
    unfiltered_df: pd.DataFrame, kept_index: pd.Index, columns: list[str]
) -> dict[str, Any]:
    """Rows in the file, rows the run kept, and missing values per column.

    Parameters
    ----------
    unfiltered_df : pandas.DataFrame
        The frame as read from disk.
    kept_index : pandas.Index
        The rows the run fit on.
    columns : list of str
        The columns that decide which rows are complete: features and
        targets.

    Returns
    -------
    dict
        Row counts, and every column with missing values and how many.
        A row can miss several columns, so the counts overlap.
    """
    missing = unfiltered_df[columns].isna().sum()
    return {
        "rows_in_file": len(unfiltered_df),
        "rows_kept": len(kept_index),
        "missing_by_column": {
            str(column): int(count)
            for column, count in missing[missing > 0]
            .sort_values(ascending=False)
            .items()
        },
    }


def describe_features(feature_names: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Each group's features that are in `feature_names`, as declared.

    Read from `model_groups`, so the record cannot disagree with the
    code that built the columns.
    """
    used = set(feature_names)
    return {
        slug: [_declaration(f) for f in group.features if f.var_name in used]
        for slug, group in MODEL_GROUPS.items()
        if any(f.var_name in used for f in group.features)
    }


def _declaration(feature: ModelVariable) -> dict[str, Any]:
    computer = feature.variable_computer
    return {
        "var_name": feature.var_name,
        "display_name": feature.display_name,
        "source": feature.source,
        "role": feature.role,
        "description": feature.description,
        "computed_as": {
            "type": type(computer).__name__,
            **{name: _plain(value) for name, value in vars(computer).items()},
        },
    }


def _plain(value: Any) -> Any:
    """Census codes are enums: keep both the code and its name."""
    if isinstance(value, Enum):
        return f"{value.value} ({type(value).__name__}.{value.name})"
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def describe_environment() -> dict[str, Any]:
    """Python, the lockfile's hash, host and Slurm job."""
    lockfile = PIPELINE_DIR.parent / "uv.lock"
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "uv_lock_sha256": file_sha256(lockfile) if lockfile.exists() else None,
        "environment_variables": {
            name: os.environ.get(name) for name in ENVIRONMENT_VARIABLES
        },
    }


def describe_raw_manifest() -> dict[str, Any] | None:
    """The raw-source checksum record as it stood: its hash and when it was written."""
    if not RAW_CHECKSUM_MANIFEST.exists():
        return None
    return {
        "path": str(RAW_CHECKSUM_MANIFEST.relative_to(PIPELINE_DIR)),
        "sha256": file_sha256(RAW_CHECKSUM_MANIFEST),
        "written": json.loads(RAW_CHECKSUM_MANIFEST.read_text()).get("written"),
    }


def start_run_metadata(
    run_dir: Path,
    git: dict[str, Any],
    settings: dict[str, Any],
    inputs: list[Path],
    sample: dict[str, Any] | None = None,
    features: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Write the metadata file as the run starts; return it for `finish_run_metadata`.

    Parameters
    ----------
    run_dir : Path
        The run directory, already created.
    git : dict
        From `git_state`.
    settings : dict
        Everything the run was parameterised by.
    inputs : list of Path
        Every file the run read.
    sample, features : dict or None
        From `describe_sample` and `describe_features`.

    Returns
    -------
    dict
        The metadata written.
    """
    metadata = {
        "run": run_dir.name,
        "started": _now(),
        "finished": None,
        "command": sys.argv,
        "code": git,
        "settings": settings,
        "inputs": [describe_input(path) for path in inputs],
        "raw_checksum_manifest": describe_raw_manifest(),
        "sample": sample,
        "features": features,
        "environment": describe_environment(),
    }
    _write(run_dir, metadata)
    return metadata


def finish_run_metadata(run_dir: Path, metadata: dict[str, Any]) -> None:
    """Stamp the finish time and list the files the run wrote."""
    metadata["finished"] = _now()
    metadata["outputs"] = sorted(
        str(path.relative_to(run_dir))
        for path in run_dir.rglob("*")
        if path.is_file() and path != run_file(run_dir, "metadata", ".json")
    )
    _write(run_dir, metadata)


def describe_source_run(run_dir: Path, files_read: list[Path]) -> dict[str, Any]:
    """A finished run a figure drew on: which of its files, and its own record.

    Runs from before 2026-10-29 have no metadata file; their commit and
    metadata then come out None rather than guessed.

    Parameters
    ----------
    run_dir : Path
        The run directory.
    files_read : list of Path
        The files of that run the figure read.

    Returns
    -------
    dict
        The run's name and path, the files read with their SHA-256, and
        the run's metadata file, commit and whether it ran on
        uncommitted changes.
    """
    metadata_path = run_file(run_dir, "metadata", ".json")
    recorded = json.loads(metadata_path.read_text()) if metadata_path.exists() else None
    return {
        "run": run_dir.name,
        "path": _shown_path(run_dir),
        "files_read": [describe_input(path) for path in files_read],
        "metadata": describe_input(metadata_path) if recorded else None,
        "commit": recorded["code"]["commit"] if recorded else None,
        "ran_on_uncommitted_changes": (
            bool(recorded["code"]["uncommitted_changes"]) if recorded else None
        ),
    }


def write_figure_metadata(
    figure_path: Path,
    git: dict[str, Any],
    settings: dict[str, Any],
    source_runs: list[dict[str, Any]],
) -> Path:
    """`metadata_<figure name>.json` beside a figure drawn from finished runs.

    Parameters
    ----------
    figure_path : Path
        The figure written.
    git : dict
        From `git_state`.
    settings : dict
        What the figure was drawn with.
    source_runs : list of dict
        From `describe_source_run`, one per run, in the figure's order.

    Returns
    -------
    Path
        The metadata file written.
    """
    metadata = {
        "figure": figure_path.name,
        "written": _now(),
        "command": sys.argv,
        "code": git,
        "settings": settings,
        "source_runs": source_runs,
        "environment": describe_environment(),
    }
    metadata_path = figure_path.with_name(f"metadata_{figure_path.stem}.json")
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str) + "\n")
    return metadata_path


def _now() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def _write(run_dir: Path, metadata: dict[str, Any]) -> None:
    run_file(run_dir, "metadata", ".json").write_text(
        json.dumps(metadata, indent=2, default=str) + "\n"
    )
