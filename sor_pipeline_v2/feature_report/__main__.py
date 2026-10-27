"""Describe one feature group on one geography: stats table plus histograms.

Pick a geographic unit and a feature group, get a folder. The unit is
named the same way the build and the regression name it, so
`--level national_tracts --states 06` here reads exactly the file that
`main_build` wrote and `regression.group_stability` fit.

Two samples are available, and they answer different questions:

  MODEL (default) describes every feature over the same rows -- the ones
  the regression keeps, complete on the FULL feature matrix and every
  target. Distributions are comparable across features and consistent
  with the R2 values, because the rows are identical.

  PER_FEATURE describes each feature over whichever rows published it, so
  the row set differs from column to column. Truer to the variable's own
  distribution in that geography, but two features in the table are then
  no longer describing the same units.

Either way the `pct_missing` column is measured on the unfiltered frame,
so what complete-case filtering cost is always visible.

Beyond the model's own feature groups, the population columns no model
fits on are reachable by name -- the decennial counts, the race-choice
shares of the Hispanic population and of the total population, and the
dominant-choice labels. `feature_report.groups` owns that mapping and
checks that no processed column is left unreachable.

Run:
  python -m feature_report --level national_tracts --states 06 --groups income
  python -m feature_report --level national_counties --groups language geography
  python -m feature_report --level national_tracts --states 06 \
      --groups share_of_hisp share_of_pop counts
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, get_args

from build_dataset.feature_manifest import MODEL_GROUPS
from build_dataset.ingest.fetch_and_store.store_df import load_df_from_parquet
from build_dataset.ingest.pl.feats.hisp_pop_feats import HISPANIC
from build_dataset.ingest.pl.feats.hisp_race_targets import (
    HISP_SOR_ALONE_PCT_OF_HISP_POP,
)
from feature_report.distributions import (
    DEFAULT_DPI,
    VECTOR_FORMATS,
    write_distributions,
)
from feature_report.glossary import GLOSSARY_MD, write_glossary
from feature_report.groups import (
    POPULATION_GROUPS,
    ReportGroupName,
    model_slugs,
    resolve_columns,
    validated_group_names,
)
from feature_report.metadata import column_meanings
from feature_report.stats import feature_stats
from regression.shared.prepare_df import prepare_df_for_regression
from regression.shared.run_config import absent_variables
from utils import config

STATS_CSV = "feature_stats.csv"

SAMPLE_NOTES = {
    "model": "only units with every model feature present (the regression's sample)",
    "per_feature": "each feature over whatever units published it",
}

SampleChoice = Literal["model", "per_feature"]


def _scope_phrase(
    level: config.GeographicBuildLevel, state_fips: Sequence[str] | None
) -> str:
    """The geography for the centred headline: "the California tract level".

    A second phrasing of the same fact as `_describe_scope`, because one
    reads as a heading and the other as a caption, and forcing one
    string to do both makes both awkward.
    """
    unit = "county" if level == "national_counties" else "tract"
    if level == "national_counties" or not state_fips:
        return f"the national {unit} level"
    names = [config.STATE_FIPS_TO_NAME[fips] for fips in sorted(state_fips)]
    return f"the {', '.join(names)} {unit} level"


def _report_dir(
    level: config.GeographicBuildLevel,
    state_fips: list[str] | None,
    feature_groups: Sequence[ReportGroupName],
    sample_choice: SampleChoice,
) -> Path:
    """`<date>_<scope>_<feature_groups>[_per_feature]`, beside the regression's runs.

    The scope and the feature_groups are both in the name because the same group
    on two geographies is two different answers, and nothing else in the
    folder records which one it was.
    """
    scope = "counties" if level == "national_counties" else "tracts"
    if state_fips:
        scope += "-" + "-".join(
            sorted(config.STATE_FIPS_TO_USPS[fips] for fips in state_fips)
        )
    name = f"{datetime.now(UTC).astimezone().date()}_{scope}_{'-'.join(feature_groups)}"
    if sample_choice != "model":
        name += f"_{sample_choice}"
    return config.DATA_DIR / "report" / "features" / name


def report_group(
    geographic_level: config.GeographicBuildLevel = "national_counties",
    state_fips: list[str] | None = None,
    feature_groups: Sequence[ReportGroupName] | None = None,
    sample_choice: SampleChoice = "model",
    dpi: int = DEFAULT_DPI,
    image_format: str = "png",
) -> Path:
    """Write one group's stats table and histograms; return the directory.

    Parameters
    ----------
    geographic_level : config.GeographicBuildLevel
        Which dataset to describe.
    state_fips : list of str or None
        Tracts only: the state scope the build covered.
    feature_groups : sequence of ReportGroupName or None
        Group names, model or population; every model group when
        omitted. Population groups are opt-in, because asking for
        everything is 127 columns. Strings from outside go through
        `groups.validated_group_names` first -- the CLI does that.
    sample_choice : SampleChoice
        "model" or "per_feature"; see the module docstring.
    dpi : int
        Raster resolution for png output; vector formats ignore it.
    image_format : str
        "png", "pdf" or "svg".

    Returns
    -------
    Path
        The directory written.

    Raises
    ------
    KeyError
        If a named group is neither a model nor a population group.
    FileNotFoundError
        If the level's processed parquet has not been built.
    """
    requested_groups: list[ReportGroupName] = (
        list(feature_groups) if feature_groups else [*MODEL_GROUPS]
    )
    input_path = config.processed_parquet_path(geographic_level, state_fips)
    unfiltered_df = load_df_from_parquet(input_path)
    exclude_variables = absent_variables(geographic_level)
    column_names = resolve_columns(requested_groups, exclude_variables)

    if sample_choice == "model":
        prepared_df = prepare_df_for_regression(
            feature_groups=model_slugs(requested_groups),
            unfiltered_df=unfiltered_df,
            exclude_variables=exclude_variables,
        )
        sample_df = unfiltered_df.loc[prepared_df.full_feature_df.index, column_names]
        hispanic_weights = prepared_df.hispanic_weights
        correlation_target = prepared_df.targets_df[HISP_SOR_ALONE_PCT_OF_HISP_POP]
    else:
        sample_df = unfiltered_df[column_names]
        hispanic_weights = unfiltered_df[HISPANIC]
        correlation_target = unfiltered_df[HISP_SOR_ALONE_PCT_OF_HISP_POP]

    unit = "counties" if geographic_level == "national_counties" else "tracts"
    scope_note = (
        f"{config.describe_geography_in_eng(geographic_level, state_fips)}: "
        f"{len(sample_df):,} of "
        f"{len(unfiltered_df):,}, {SAMPLE_NOTES[sample_choice]}"
    )

    output_dir = _report_dir(
        geographic_level, state_fips, requested_groups, sample_choice
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    stats = feature_stats(
        sample_df,
        unfiltered_df,
        hispanic_weights=hispanic_weights,
        correlation_target=correlation_target,
    )
    stats.to_csv(output_dir / STATS_CSV, index=False)
    meanings = column_meanings()
    figures = write_distributions(
        sample_df,
        output_dir,
        unit,
        scope_note,
        _scope_phrase(geographic_level, state_fips),
        meanings,
        dpi,
        image_format,
    )
    write_glossary(output_dir, scope_note, list(sample_df.columns))

    print(
        f"feature report -> {output_dir}\n"
        f"{scope_note}\n"
        f"groups: {', '.join(requested_groups)}\n"
        f"  {len(stats)} columns -> {STATS_CSV}\n"
        f"  {len(figures)} {image_format} figures"
        f"{'' if image_format in VECTOR_FORMATS else f' at {dpi} dpi'}"
        " (one per column, plus the feature grid)\n"
        f"  column glossary -> {GLOSSARY_MD}"
    )
    return output_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m feature_report",
        description="Distributions and descriptive stats for a feature group.",
    )
    parser.add_argument(
        "--level",
        choices=list(get_args(config.GeographicBuildLevel)),
        default="national_counties",
        help="which dataset to describe (default: national_counties)",
    )
    parser.add_argument(
        "--states",
        nargs="+",
        default=None,
        metavar="FIPS",
        help="tracts only: the state scope the build covered, e.g. --states 06 "
        "reads processed_states-06.parquet; omit for the national tract file",
    )
    parser.add_argument(
        "--groups",
        nargs="+",
        default=None,
        metavar="G",
        help="groups to describe (default: every model group). Model groups: "
        f"{list(MODEL_GROUPS)}. Population groups, opt-in by name: "
        f"{list(POPULATION_GROUPS)}",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"raster resolution for png output (default and minimum: {DEFAULT_DPI})",
    )
    parser.add_argument(
        "--format",
        dest="image_format",
        choices=("png", *VECTOR_FORMATS),
        default="png",
        help="figure format; pdf and svg stay sharp at any zoom and ignore --dpi",
    )
    parser.add_argument(
        "--sample",
        choices=list(get_args(SampleChoice)),
        default="model",
        help="'model' describes every feature over the regression's "
        "complete-case rows (default); 'per_feature' describes each feature "
        "over its own non-null rows",
    )
    args = parser.parse_args()
    if args.dpi < DEFAULT_DPI:
        parser.error(f"--dpi must be at least {DEFAULT_DPI}")
    return args


if __name__ == "__main__":
    args = _parse_args()
    report_group(
        geographic_level=args.level,
        state_fips=args.states,
        feature_groups=validated_group_names(args.groups or []) or None,
        sample_choice=args.sample,
        dpi=args.dpi,
        image_format=args.image_format,
    )
