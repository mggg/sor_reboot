"""Collect every region's Moran's I results for a run into one spreadsheet.

Each region folder under ``<run_dir>/spatial/`` holds a ``<region>_moran.csv``
with columns ``method, key, I, EI, p_sim``. This script stacks them into one
long-format CSV with a ``region`` column added (``spatial/moran_all.csv``,
keeps every stat), plus a readable wide view with regions as columns and
Moran's I as the cells (``spatial/moran_wide.csv``).

Usage (from the sor_reboot directory)::

    python -m sor_pipeline.utils.collect_moran                 # run from config.py
    python -m sor_pipeline.utils.collect_moran path/to/run_dir # any other run
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import config

# Column order for the wide sheet: whole-map first, then regions roughly
# east-to-west, then the small non-contiguous ones. Selecting by name also
# raises a KeyError if an expected region is missing from the run.
REGION_ORDER = [
    "contiguous_us",
    "northeast",
    "midwest",
    "south",
    "contiguous_west",
    "alaska",
    "puerto_rico",
]


def collect_moran(run_dir: Path) -> pd.DataFrame:
    """Stack every ``*_moran.csv`` under ``run_dir/spatial/`` into one frame.

    Regions with no CSV (e.g. skipped for having too few units) are naturally
    absent; raises if the glob finds nothing at all, which usually means
    ``run_dir`` isn't a run directory.
    """
    frames = []
    for csv_path in sorted(run_dir.glob("spatial/*/*_moran.csv")):
        region = csv_path.parent.name
        frames.append(pd.read_csv(csv_path).assign(region=region))
    if not frames:
        raise FileNotFoundError(f"no *_moran.csv found under {run_dir / 'spatial'}")
    combined = pd.concat(frames, ignore_index=True)
    return combined[["region", "method", "key", "I", "EI", "p_sim"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "run_dir",
        nargs="?",
        type=Path,
        default=config.NATIONAL_RUN_DIR,
        help="run directory to collect from (default: the run in utils/config.py)",
    )
    args = parser.parse_args()

    combined = collect_moran(args.run_dir)
    out_path = args.run_dir / "spatial" / "moran_all.csv"
    combined.to_csv(out_path, index=False)
    print(
        f"Wrote {len(combined)} rows ({combined['region'].nunique()} regions) "
        f"-> {out_path}"
    )

    # Wide view for reading: rows = (method, rate), columns = regions, cells = I.
    # .pivot (not .pivot_table) so duplicate rows raise instead of being averaged.
    wide = combined.pivot(index=["method", "key"], columns="region", values="I")
    wide = wide[REGION_ORDER]
    wide_path = args.run_dir / "spatial" / "moran_wide.csv"
    wide.to_csv(wide_path)
    print(f"Wrote wide I table ({len(wide)} rows) -> {wide_path}")


if __name__ == "__main__":
    main()
