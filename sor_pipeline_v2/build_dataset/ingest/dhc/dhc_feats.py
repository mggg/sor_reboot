"""DHC features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import DHC_P2
from build_dataset.ingest.declarations.denominators import Denominator
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
)

DHC_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="DHC",
        var_name="URBANSHARE",
        display_name="Urban population share",
        description=(
            "Share of the unit's total population living in an urban "
            "area (2020 Census urban/rural classification)"
        ),
        variable_computer=FractionalShare(
            numerator_codes=[DHC_P2.URBAN],
            denominator_codes=[Denominator.TOTAL_POPULATION_DHC],
        ),
    ),
]
