import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from build_dataset.feature_manifest import (
    MODEL_GROUPS,
    TRACT_ABSENT_VARIABLES,
    SlugGroupName,
)
from build_dataset.ingest.pl.feats.hisp_pop_feats import HISPANIC
from build_dataset.ingest.pl.feats.hisp_race_targets import (
    HISP_SOR_ALONE_PCT_OF_HISP_POP,
    HISP_WHITE_ALONE_PCT_OF_HISP_POP,
    HISP_WHITE_PCT_OF_HISP_POP,
    HISP_WHITE_SOR_PCT_OF_HISP_POP,
)
from model_utils.split import SplitGrouping
from utils import config

# Target column -> the short label used in output tables.
REGRESSION_TARGETS = {
    HISP_SOR_ALONE_PCT_OF_HISP_POP: "Hisp Share SOR Alone",
    HISP_WHITE_SOR_PCT_OF_HISP_POP: "Hisp Share White and SOR",
    HISP_WHITE_ALONE_PCT_OF_HISP_POP: "Hisp Share White Alone",
    HISP_WHITE_PCT_OF_HISP_POP: "Hisp Share White in Combination",
}

WEIGHT_COL = HISPANIC  # the weight that turns a places question into a people one
FULL = "full"  # the baseline pseudo-group: the entire feature matrix
# An ablation matrix is named for what it drops, e.g. "full-minus-geography".
FULL_MINUS = "full-minus-"


@dataclass()
class RegressionParameters:
    """Default tree hyperparameters from both tree models."""

    max_depth: int = 8
    n_estimators: int = 100
    learning_rate: float = 0.1  # lgbm only
    num_leaves: int = 31  # lgbm only


@dataclass(frozen=True)
class FullRegressionModelRunParams:
    """Everything one group-stability run is parameterized by."""

    rng_seeds: list[int]
    regression_tree_params: RegressionParameters
    feature_groups: list[SlugGroupName]
    top_percent: int | None = None
    bottom_percent: int | None = None
    include_full_baseline: bool = True
    # Groups to ABLATE: each run also fits the full matrix with these
    # groups' features removed, alongside the untouched full baseline, so
    # one run yields the comparison an ablation is asking for.
    exclude_groups: list[SlugGroupName] = field(default_factory=list)
    # Which dataset to fit. `state_fips` scopes a tract run to the states
    # that build covered, and both appear in the run directory's name, so
    # a tract run cannot overwrite a county run's outputs.
    geo_level: config.GeographicBuildLevel = "national_counties"
    state_fips: list[str] | None = None
    # Which tracts each seed's train/test split keeps together; see model_utils.split.
    split_grouping: SplitGrouping = "none"

    def __post_init__(self) -> None:
        if self.top_percent is not None and self.bottom_percent is not None:
            raise ValueError("pass top_percent or bottom_percent, not both")

        if self.state_fips and self.geo_level == "national_counties":
            raise ValueError(
                "state_fips scopes a tract build; the county build is one "
                "national pull with no state subsets"
            )

        if self.split_grouping == "county" and self.geo_level == "national_counties":
            raise ValueError(
                "county grouping keeps a county's tracts together; at the "
                "county level every row is already its own county"
            )

        if self.feature_groups is None:
            object.__setattr__(self, "feature_groups", list(MODEL_GROUPS))

        if self.feature_groups is not None:
            unknown = [s for s in self.feature_groups if s not in MODEL_GROUPS]
            if unknown:
                raise ValueError(
                    f"unknown feature group(s) {unknown}; known: {list(MODEL_GROUPS)}"
                )

        unknown_excluded = [s for s in self.exclude_groups if s not in MODEL_GROUPS]
        if unknown_excluded:
            raise ValueError(
                f"unknown excluded group(s) {unknown_excluded}; known: {list(MODEL_GROUPS)}"
            )
        if self.exclude_groups and not self.include_full_baseline:
            raise ValueError("an ablation needs the full baseline to compare against")


# The inverse of what `create_run_dir` writes into the name: "_tracts"
# optionally followed by "-" and the state codes it covered.
# Runs before 2026-10-27 spelled the states as FIPS codes ("06"), later
# ones as USPS codes ("CA"); both still read back.
RUN_DIR_SCOPE = re.compile(
    r"_tracts(?:-(?P<states>(?:[0-9]{2}|[A-Z]{2})(?:-(?:[0-9]{2}|[A-Z]{2}))*))?"
)
_USPS_TO_STATE_FIPS = {usps: fips for fips, usps in config.STATE_FIPS_TO_USPS.items()}


def scope_from_run_dir(
    name: str,
) -> tuple[config.GeographicBuildLevel, list[str] | None]:
    """The geography a run directory's NAME encodes.

    Figures can be redrawn from a finished run's CSVs without refitting,
    and at that point the directory name is the only record of what the
    run covered. Kept next to `create_run_dir`, which writes the name
    this reads, so the pair cannot drift apart unnoticed.

    Parameters
    ----------
    name : str
        A run directory's name, e.g. "2026-10-18_seeds-1-50_tracts-CA".

    Returns
    -------
    tuple
        The level, and the state codes for a scoped tract run (None for
        a national one).
    """
    found = RUN_DIR_SCOPE.search(name)
    if not found:
        return "national_counties", None
    states = found.group("states")
    if not states:
        return "national_tracts", None
    return "national_tracts", [
        _USPS_TO_STATE_FIPS.get(code, code) for code in states.split("-")
    ]


def scope_suffix(
    level: config.GeographicBuildLevel, state_fips: Sequence[str] | None = None
) -> str:
    """The geography as an output-directory suffix; `scope_from_run_dir` reads it back.

    Every driver that writes a run directory appends this, so a tract run
    cannot land on top of the county run it would otherwise be named
    identically to. Counties get "" -- they are the default and their
    directory names predate levels existing.

    Parameters
    ----------
    level : config.GeographicBuildLevel
        The dataset the run covered.
    state_fips : sequence of str or None
        Tracts only: the state scope. None means the national file.

    Returns
    -------
    str
        "" for counties, "_tracts" nationally, "_tracts-CA" for one state.
    """
    if level == "national_counties":
        return ""
    if not state_fips:
        return "_tracts"
    return "_tracts-" + "-".join(
        sorted(config.STATE_FIPS_TO_USPS[fips] for fips in state_fips)
    )


def absent_variables(level: config.GeographicBuildLevel) -> tuple[str, ...]:
    """Predictors the level does not have, for `prepare_df_for_regression`.

    Parameters
    ----------
    level : config.GeographicBuildLevel
        The dataset being fit.

    Returns
    -------
    tuple of str
        Empty for counties, which have every declared predictor; the
        manifest's tract list otherwise.
    """
    return () if level == "national_counties" else TRACT_ABSENT_VARIABLES


def create_run_dir(run_params: FullRegressionModelRunParams) -> Path:
    """`<date>_seeds-<lo>-<hi>[_<param>-<v> for non-default hyperparameters]`.

    The seed range is always in the name; hyperparameters appear only when
    they differ from the defaults, so a default run's name stays short and a
    tuned run says what was tuned.
    """
    if len(run_params.rng_seeds) > 1:
        name = f"{datetime.now(UTC).astimezone().date()}_seeds-{min(run_params.rng_seeds)}-{max(run_params.rng_seeds)}"
    else:
        name = (
            f"{datetime.now(UTC).astimezone().date()}_seeds-{run_params.rng_seeds[0]}"
        )
    # The level only when it is not the county default, so a county run's
    # name is unchanged and a tract run is unmistakable.
    name += scope_suffix(run_params.geo_level, run_params.state_fips)
    defaults = asdict(RegressionParameters())
    for regression_param, value in asdict(run_params.regression_tree_params).items():
        if value != defaults[regression_param]:
            name += f"_{regression_param.replace('_', '-')}-{value}"
    if run_params.top_percent is not None:
        name += f"_top-{run_params.top_percent:g}pct"
    if run_params.bottom_percent is not None:
        name += f"_bottom-{run_params.bottom_percent:g}pct"
    if run_params.split_grouping != "none":
        name += f"_grouped-by-{run_params.split_grouping}"
    # Only a subset run names its groups; the every-group default stays
    # short. Named from the matrices actually fit, so `--groups full` --
    # which leaves feature_groups empty, the baseline being a runner
    # concept -- reads "_groups-full" rather than a dangling "_groups-".
    if set(run_params.feature_groups) != set(MODEL_GROUPS):
        fitted = [FULL] if run_params.include_full_baseline else []
        fitted += list(run_params.feature_groups)
        name += "_groups-" + "-".join(fitted)
    if run_params.exclude_groups:
        name += "_without-" + "-".join(run_params.exclude_groups)
    return config.DATA_DIR / "prediction" / "regression" / name
