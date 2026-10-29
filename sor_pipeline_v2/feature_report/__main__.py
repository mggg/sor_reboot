"""Describe one feature group on one geography: stats table plus histograms.

Pick a geographic unit and a feature group, get a folder. The unit is
named the same way the build and the regression name it, so
`--level national_tracts --states 06` here reads exactly the file that
`main_build` wrote and `regression.group_stability` fit.

Two row selections are available, and they answer different questions:

  COMPLETE_CASE (default) describes every feature over the same rows -- the ones
  the regression keeps, complete on the FULL feature matrix and every
  target. Distributions are comparable across features and consistent
  with the R2 values, because the rows are identical.

  AVAILABLE_CASE describes each feature over whichever rows published it, so
  the row set differs from column to column. Truer to the variable's own
  distribution in that geography, but two features in the table are then
  no longer describing the same units.

Either way the `pct_of_file_missing` column is measured on the unfiltered frame,
so what complete-case filtering cost is always visible.

Groups are the model's predictor groups, plus "targets" for the four
shares the regression predicts; `feature_report.groups` maps each name to
its columns.

Run:
  python -m feature_report --level national_tracts --states 06 --groups income
  python -m feature_report --level national_counties --groups language geography
  python -m feature_report --level national_tracts --states 06 --groups targets
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import InitVar, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, get_args

from build_dataset.ingest.fetch_and_store.store_df import load_df_from_parquet
from build_dataset.ingest.pl.feats.hisp_pop_feats import HISPANIC
from build_dataset.ingest.pl.feats.hisp_race_targets import (
    HISP_SOR_ALONE_PCT_OF_HISP_POP,
)
from build_dataset.model_groups import MODEL_GROUPS
from feature_report.column_meanings import column_meanings
from feature_report.distributions import (
    DEFAULT_DPI,
    VECTOR_FORMATS,
    write_distributions,
)
from feature_report.glossary import GLOSSARY_MD, write_glossary
from feature_report.groups import (
    ReportGroupName,
    model_group_names,
    resolve_columns,
    validated_group_names,
)
from feature_report.stats import feature_stats
from regression.shared.prepare_df import prepare_df_for_regression
from regression.shared.run_config import absent_variables
from utils import config

STATS_CSV = "feature_stats.csv"

ROW_SELECTION_NOTES = {
    "complete_case": "only units with every model feature present (the regression's sample)",
    "available_case": "each feature over whatever units published it",
}

RowSelection = Literal["complete_case", "available_case"]
ImageFormat = Literal["png", "pdf", "svg"]


@dataclass(frozen=True)
class FeatureReportParams:
    """Everything one feature report is parameterized by, checked on creation.

    Attributes
    ----------
    geographic_level : config.GeographicBuildLevel
        Which dataset to describe.
    state_fips : list of str or None
        Tracts only: the state scope the build covered.
    requested_groups : sequence of str or None
        Model group names, or "targets"; every model group when
        omitted, so the targets are opt-in. Checked and narrowed to
        ReportGroupName here, so strings from the CLI can be passed as is.
        A constructor argument only; the checked list is `feature_groups`.
    row_selection : RowSelection
        "complete_case" or "available_case"; see the module docstring.
    dpi : int
        Raster resolution for png output; vector formats ignore it.
    image_format : ImageFormat
        "png", "pdf" or "svg".
    feature_groups : list of ReportGroupName
        Set from `requested_groups` on creation, not passed in.

    Raises
    ------
    ValueError
        If a value is outside what the report can use: an unknown level,
        row selection, or image format; states on a county report or an
        unknown state FIPS code; a dpi below DEFAULT_DPI.
    KeyError
        If a named group is neither a model group nor "targets".
    """

    geographic_level: config.GeographicBuildLevel = "national_counties"
    state_fips: list[str] | None = None
    requested_groups: InitVar[Sequence[str] | None] = None
    row_selection: RowSelection = "complete_case"
    dpi: int = DEFAULT_DPI
    image_format: ImageFormat = "png"
    feature_groups: list[ReportGroupName] = field(init=False)

    def __post_init__(self, requested_groups: Sequence[str] | None) -> None:
        levels = get_args(config.GeographicBuildLevel)
        if self.geographic_level not in levels:
            raise ValueError(
                f"unknown geographic level {self.geographic_level!r}; known: {list(levels)}"
            )

        if self.state_fips and self.geographic_level == "national_counties":
            raise ValueError(
                "state_fips scopes a tract build; the county build is one "
                "national pull with no state subsets"
            )
        if self.state_fips:
            unknown_states = [
                fips
                for fips in self.state_fips
                if fips not in config.STATE_FIPS_TO_USPS
            ]
            if unknown_states:
                raise ValueError(f"unknown state FIPS code(s) {unknown_states}")

        object.__setattr__(
            self,
            "feature_groups",
            (
                validated_group_names(requested_groups)
                if requested_groups
                else [*MODEL_GROUPS]
            ),
        )

        if self.row_selection not in get_args(RowSelection):
            raise ValueError(
                f"unknown row selection {self.row_selection!r}; "
                f"known: {list(get_args(RowSelection))}"
            )

        if self.dpi < DEFAULT_DPI:
            raise ValueError(f"dpi must be at least {DEFAULT_DPI}, got {self.dpi}")

        if self.image_format not in get_args(ImageFormat):
            raise ValueError(
                f"unknown image format {self.image_format!r}; "
                f"known: {list(get_args(ImageFormat))}"
            )


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
    row_selection: RowSelection,
) -> Path:
    """`<date>_<scope>_<feature_groups>[_available_case]`, beside the regression's runs.

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
    if row_selection != "complete_case":
        name += f"_{row_selection}"
    return config.DATA_DIR / "report" / "features" / name


def report_group(params: FeatureReportParams) -> Path:
    """Write one group's stats table and histograms; return the directory.

    Parameters
    ----------
    params : FeatureReportParams
        What to describe and how; its values are checked on creation.

    Returns
    -------
    Path
        The directory written.

    Raises
    ------
    FileNotFoundError
        If the level's processed parquet has not been built.
    """
    geographic_level = params.geographic_level
    state_fips = params.state_fips
    row_selection = params.row_selection
    requested_groups = params.feature_groups
    input_path = config.processed_parquet_path(geographic_level, state_fips)
    unfiltered_df = load_df_from_parquet(input_path)
    exclude_variables = absent_variables(geographic_level)
    column_names = resolve_columns(requested_groups, exclude_variables)

    if row_selection == "complete_case":
        prepared_df = prepare_df_for_regression(
            feature_groups=model_group_names(requested_groups),
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
        f"{len(unfiltered_df):,}, {ROW_SELECTION_NOTES[row_selection]}"
    )

    output_dir = _report_dir(
        geographic_level, state_fips, requested_groups, row_selection
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
        params.dpi,
        params.image_format,
    )
    write_glossary(output_dir, scope_note, list(sample_df.columns))

    print(
        f"feature report -> {output_dir}\n"
        f"{scope_note}\n"
        f"groups: {', '.join(requested_groups)}\n"
        f"  {len(stats)} columns -> {STATS_CSV}\n"
        f"  {len(figures)} {params.image_format} figures"
        f"{'' if params.image_format in VECTOR_FORMATS else f' at {params.dpi} dpi'}"
        " (one per column, plus the feature grid)\n"
        f"  column glossary -> {GLOSSARY_MD}"
    )
    return output_dir


def _parse_args() -> FeatureReportParams:
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
        f"{list(MODEL_GROUPS)}; or 'targets' for the four regression "
        "targets",
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
        choices=list(get_args(ImageFormat)),
        default="png",
        help="figure format; pdf and svg stay sharp at any zoom and ignore --dpi",
    )
    parser.add_argument(
        "--rows",
        dest="row_selection",
        choices=list(get_args(RowSelection)),
        default="complete_case",
        help="'complete_case' describes every feature over the regression's "
        "complete-case rows (default); 'available_case' describes each feature "
        "over its own non-null rows",
    )
    args = parser.parse_args()
    try:
        return FeatureReportParams(
            geographic_level=args.level,
            state_fips=args.states,
            requested_groups=args.groups,
            row_selection=args.row_selection,
            dpi=args.dpi,
            image_format=args.image_format,
        )
    except (ValueError, KeyError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    report_group(_parse_args())
