"""Shared checkpoint helper for the pipeline drivers.

Each driver step writes an output to the data tree; before re-running an expensive
step the driver asks whether to redo it. Centralized here so `run_national` and
`run_prediction` behave identically instead of each carrying their own copy.
"""

from __future__ import annotations

from pathlib import Path


def confirm_rerun(path: Path, step: str) -> bool:
    """Return True if `step` should run.

    Runs unconditionally when the output doesn't exist yet. If it does exist, prompt
    the user (default "no"). A directory counts as produced only if it is non-empty.
    In a non-interactive shell (no stdin), an existing output is left as-is rather
    than blocking.
    """
    produced = path.exists() and (any(path.iterdir()) if path.is_dir() else True)
    if not produced:
        return True
    try:
        resp = input(
            f"  [{step}] output already exists ({path.name}). Re-run this step? [y/N]: "
        )
    except EOFError:
        resp = ""  # non-interactive: don't re-run
    return resp.strip().lower() in {"y", "yes"}
