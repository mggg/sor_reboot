"""Income and Affluence features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.feature_utils import ModelFeature

INCOME_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="B19301I",
        table_code="B19301I_001E",
        var_name="HISPPERCAPINCOME",
        description="Per capita income, Hispanic population (2020 dollars)",
        numerator_codes=("B19301I_001E",),
        denominator_codes=(),
    ),
    ModelFeature(
        source_table="B17001I",
        table_code=None,
        var_name="HISPPOVERTY",
        description="Income in the past 12 months below the poverty level",
        numerator_codes=("B17001I_002E",),
        denominator_codes=("B17001I_001E",),
    ),
    ModelFeature(
        source_table="B22005I",
        table_code=None,
        var_name="HISPSNAP",
        description="Received SNAP/Food Stamps in the past 12 months",
        numerator_codes=("B22005I_002E",),
        denominator_codes=("B22005I_001E",),
    ),
    ModelFeature(
        source_table="B25003I",
        table_code=None,
        var_name="HISPOWNEROCC",
        description="Owner-occupied (renter-occupied is the exact complement)",
        numerator_codes=("B25003I_002E",),
        denominator_codes=("B25003I_001E",),
    ),
    ModelFeature(
        source_table="B25014I",
        table_code=None,
        var_name="HISPCROWDING",
        description="Crowded housing: 1.01 or more occupants per room",
        numerator_codes=("B25014I_003E",),
        denominator_codes=("B25014I_001E",),
    ),
    ModelFeature(
        source_table="B28009I",
        table_code=None,
        var_name="HISPBROADBAND",
        description="Has a computer with a broadband internet subscription",
        numerator_codes=("B28009I_004E",),
        denominator_codes=("B28009I_001E",),
    ),
    ModelFeature(
        source_table="B28009I",
        table_code=None,
        var_name="HISPCOMPUTERNOBROADBAND",
        description="Has a computer but no broadband (dial-up only, or no subscription)",
        numerator_codes=("B28009I_003E", "B28009I_005E"),
        denominator_codes=("B28009I_001E",),
    ),
    ModelFeature(
        source_table="B28009I",
        table_code=None,
        var_name="HISPNOCOMPUTER",
        description="No computer in the household",
        numerator_codes=("B28009I_006E",),
        denominator_codes=("B28009I_001E",),
    ),
]
