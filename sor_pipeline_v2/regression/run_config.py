from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from build_dataset.feature_manifest import MODEL_GROUPS, SlugGroupName
from utils import config

REGRESSION_TARGETS = {
    "Hisp_SOR_Alone_Pct_of_Hisp_Pop": "Hisp Share SOR Alone",
    "Hisp_White_SOR_Pct_of_Hisp_Pop": "Hisp Share White and SOR",
    "Hisp_White_Alone_Pct_of_Hisp_Pop": "Hisp Share White Alone",
    "Hisp_White_Pct_of_Hisp_Pop": "Hisp Share White in Combination",
}

WEIGHT_COL = "HISPANIC"  # the weight that turns a places question into a people one
FULL = "full"  # the baseline pseudo-group: the entire feature matrix


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
    feature_groups: list[SlugGroupName] | None
    top_percent: float | None = None
    bottom_percent: float | None = None
    include_full_baseline: bool = True

    def __post_init__(self) -> None:
        if self.top_percent is not None and self.bottom_percent is not None:
            raise ValueError("pass top_percent or bottom_percent, not both")

        if self.feature_groups is None:
            object.__setattr__(self, "feature_groups", list(MODEL_GROUPS))

        if self.feature_groups is not None:
            unknown = [s for s in self.feature_groups if s not in MODEL_GROUPS]
            if unknown:
                raise ValueError(
                    f"unknown feature group(s) {unknown}; "
                    f"known: {list(MODEL_GROUPS)}"
                )


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
    defaults = asdict(RegressionParameters())
    for regression_param, value in asdict(run_params.regression_tree_params).items():
        if value != defaults[regression_param]:
            name += f"_{regression_param.replace('_', '-')}-{value}"
    if run_params.top_percent is not None:
        name += f"_top-{run_params.top_percent:g}pct"
    if run_params.bottom_percent is not None:
        name += f"_bottom-{run_params.bottom_percent:g}pct"
    # Only a subset run names its groups; the every-group default stays short.
    if set(run_params.feature_groups) != set(MODEL_GROUPS):
        name += "_groups-" + "-".join(run_params.feature_groups)
    return config.DATA_DIR / "prediction" / "regression" / name
