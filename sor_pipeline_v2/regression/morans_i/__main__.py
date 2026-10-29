"""Moran's I of the SOR-alone share across one tract map: are neighbours alike?

The group-stability runs split tracts into train and test at random by
default. If neighbouring tracts have similar SOR-alone shares, a random
split leaves most test tracts with look-alike neighbours in training, and
the test score is optimistic -- the reason for `--split-grouping county`.
This measures that similarity with PySAL's standard statistic.

Neighbours are tracts that share a border (Rook contiguity, `libpysal`),
row-standardised. Tracts with no neighbour in the sample are dropped before
the weights are rebuilt, since Moran's I is undefined for them.

Two versions, on the same tracts and weights:
- raw: the share as the models see it, HSOR / HISPANIC.
- Empirical Bayes (`esda.smoothing`): each share pulled toward the map's
  overall rate, harder for tracts with few Hispanic residents. Noisy small
  tracts push Moran's I toward 0, so the smoothed version shows how much of
  the raw value that noise is hiding.

The sample is the scored runs' own: tracts complete on the full matrix and
every target, as `prepare_df_for_regression` keeps them.

Run: `python -m regression.morans_i [--states FIPS ...] [--seed N]`.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import geopandas as gpd
import numpy as np
import pandas as pd
from esda.moran import Moran
from esda.smoothing import Empirical_Bayes
from libpysal.weights import Rook

from build_dataset.ingest.geometry.geometry_api import (
    TRACT_GEOMETRY_2020_PARQUET_TEMPLATE,
)
from regression.shared.prepare_df import prepare_df_for_regression
from regression.shared.run_config import absent_variables, run_file, scope_suffix
from regression.shared.run_metadata import (
    describe_sample,
    finish_run_metadata,
    git_state,
    start_run_metadata,
    warn_if_uncommitted,
)
from utils import config

LEVEL: config.GeographicBuildLevel = "national_tracts"
SOR_ALONE_COUNT = "HSOR"  # Hispanic, SOR alone; / HISPANIC is the target share


def load_sample_tracts(
    state_fips: list[str] | None,
) -> tuple[gpd.GeoDataFrame, list[Path], dict]:
    """The scored runs' tracts, with their polygons, SOR count and Hispanic count.

    Parameters
    ----------
    state_fips : list of str or None
        The state scope; None reads the national tract file.

    Returns
    -------
    tuple
        One row per sample tract (GEOID, HSOR, HISPANIC, the SOR-alone
        share, and the tract polygon); every file read; and the sample
        record for the run's metadata.
    """
    input_path = config.processed_parquet_path(LEVEL, state_fips)
    unfiltered_df = pd.read_parquet(input_path)
    prepared = prepare_df_for_regression(
        feature_groups=[],
        unfiltered_df=unfiltered_df,
        exclude_variables=absent_variables(LEVEL),
    )
    sample = unfiltered_df.loc[
        prepared.full_feature_df.index, ["GEOID", SOR_ALONE_COUNT, "HISPANIC"]
    ]
    sample["sor_alone_share"] = sample[SOR_ALONE_COUNT] / sample["HISPANIC"]

    states_in_sample = sorted(sample["GEOID"].str[:2].unique())
    geometry_paths = [
        config.RAW_NATIONAL_DIR
        / TRACT_GEOMETRY_2020_PARQUET_TEMPLATE.format(state_fips=fips)
        for fips in states_in_sample
    ]
    polygons = pd.concat(
        [gpd.read_parquet(path)[["GEOID", "geometry"]] for path in geometry_paths],
        ignore_index=True,
    )
    tracts = polygons.merge(sample, on="GEOID", how="inner", validate="one_to_one")
    if len(tracts) != len(sample):
        raise ValueError(
            f"{len(sample) - len(tracts):,} sample tracts have no 2020 polygon"
        )
    null_polygons = tracts["geometry"].isna()
    if null_polygons.any():
        by_state = tracts.loc[null_polygons, "GEOID"].str[:2].value_counts()
        raise ValueError(
            f"{int(null_polygons.sum()):,} sample tracts have an empty polygon in "
            f"the geometry cache, by state FIPS: {by_state.to_dict()}"
        )
    sample_record = describe_sample(
        unfiltered_df,
        prepared.full_feature_df.index,
        [*prepared.full_feature_df.columns, *prepared.targets_df.columns],
    )
    return (
        gpd.GeoDataFrame(tracts, geometry="geometry"),
        [input_path, *geometry_paths],
        sample_record,
    )


def rook_weights_without_islands(
    tracts: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, Rook, int]:
    """Rook weights, row-standardised, after dropping tracts with no neighbour.

    Returns
    -------
    tuple
        The tracts kept, their weights, and how many tracts were dropped.
    """
    tracts = tracts.reset_index(drop=True)
    weights = _rook(tracts)
    n_islands = len(weights.islands)
    if n_islands:
        tracts = tracts.drop(index=weights.islands).reset_index(drop=True)
        weights = _rook(tracts)
    weights.transform = "r"
    return tracts, weights, n_islands


def _rook(tracts: gpd.GeoDataFrame) -> Rook:
    # libpysal types the result as Rook or its sparse WSP form; WSP comes
    # back only when asked for (sparse=True), so this is always a Rook.
    return cast(Rook, Rook.from_dataframe(tracts, use_index=False))


def run_morans_i(state_fips: list[str] | None = None, seed: int = 1) -> Path:
    """Raw and Empirical Bayes Moran's I for one scope; writes one CSV row.

    Parameters
    ----------
    state_fips : list of str or None
        The state scope, as the group-stability runs take it; None is the
        national tract file.
    seed : int
        Seeds the permutations behind the pseudo p-values.

    Returns
    -------
    Path
        The CSV written.
    """
    git = git_state()
    warn_if_uncommitted(git)
    tracts, inputs, sample_record = load_sample_tracts(state_fips)
    tracts, weights, n_islands = rook_weights_without_islands(tracts)

    # esda draws its permutations from numpy's global generator.
    np.random.seed(seed)
    raw = Moran(tracts["sor_alone_share"].to_numpy(), weights)
    smoothed_share = Empirical_Bayes(
        tracts[SOR_ALONE_COUNT].to_numpy(), tracts["HISPANIC"].to_numpy()
    ).r.flatten()
    smoothed = Moran(smoothed_share, weights)

    geography_in_eng = config.describe_geography_in_eng(LEVEL, state_fips)
    result = {
        "scope": geography_in_eng,
        "n_tracts": len(tracts),
        "n_islands_dropped": n_islands,
        "mean_neighbours": weights.mean_neighbors,
        "expected_i_if_random": raw.EI,
        "raw_i": raw.I,
        "raw_p": raw.p_sim,
        "empirical_bayes_i": smoothed.I,
        "empirical_bayes_p": smoothed.p_sim,
        "permutations": raw.permutations,
        "seed": seed,
    }
    print(
        f"{geography_in_eng}: {len(tracts):,} tracts ({n_islands:,} with no "
        f"neighbour dropped), {weights.mean_neighbors:.1f} neighbours on average\n"
        f"  Moran's I, raw SOR-alone share:  {raw.I:.3f} (p = {raw.p_sim:.3f})\n"
        f"  Moran's I, Empirical Bayes:      {smoothed.I:.3f} (p = {smoothed.p_sim:.3f})\n"
        f"  expected if the map were random: {raw.EI:.4f}"
    )

    output_dir = (
        config.DATA_DIR
        / "prediction"
        / "regression"
        / (
            f"morans_i_{datetime.now(UTC).astimezone().date()}"
            f"{scope_suffix(LEVEL, state_fips)}"
        )
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = start_run_metadata(
        output_dir,
        git,
        settings={
            "state_fips": state_fips,
            "seed": seed,
            "value": f"{SOR_ALONE_COUNT} / HISPANIC (SOR-alone share)",
            "weights": "Rook contiguity, row-standardised, no-neighbour tracts dropped",
            "permutations": raw.permutations,
        },
        inputs=inputs,
        sample=sample_record,
    )
    output_path = run_file(output_dir)
    pd.DataFrame([result]).to_csv(output_path, index=False)
    finish_run_metadata(output_dir, metadata)
    print(f"output -> {output_path}")
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m regression.morans_i",
        description="Moran's I of the tract SOR-alone share, raw and Empirical Bayes.",
    )
    parser.add_argument(
        "--states",
        nargs="+",
        default=None,
        metavar="FIPS",
        help="the state scope the build covered, e.g. --states 06 reads "
        "processed_states-06.parquet; omit for the national tract file",
    )
    parser.add_argument(
        "--seed", type=int, default=1, help="seeds the permutation p-values"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_morans_i(args.states, args.seed)
