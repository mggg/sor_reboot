"""Racial and Ethnic Composition features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.feature_utils import ModelFeature

RACIAL_ETHNIC_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="B03002",
        table_code=None,
        var_name="NONHISPANICWHITESHARE",
        description="Non-Hispanic White alone",
        numerator_codes=("B03002_003E",),
        denominator_codes=("B03002_001E",),
    ),
    ModelFeature(
        source_table="B03002",
        table_code=None,
        var_name="NONHISPANICBLACKSHARE",
        description="Non-Hispanic Black or African American alone",
        numerator_codes=("B03002_004E",),
        denominator_codes=("B03002_001E",),
    ),
    ModelFeature(
        source_table="B03002",
        table_code=None,
        var_name="NONHISPANICAIANSHARE",
        description="Non-Hispanic American Indian and Alaska Native alone",
        numerator_codes=("B03002_005E",),
        denominator_codes=("B03002_001E",),
    ),
    ModelFeature(
        source_table="B03002",
        table_code=None,
        var_name="NONHISPANICASIANSHARE",
        description="Non-Hispanic Asian alone",
        numerator_codes=("B03002_006E",),
        denominator_codes=("B03002_001E",),
    ),
    ModelFeature(
        source_table="B03002",
        table_code=None,
        var_name="NONHISPANICMULTISHARE",
        description="Non-Hispanic, two or more races -- the county's non-Hispanic propensity for "
        "multiracial reporting",
        numerator_codes=("B03002_009E",),
        denominator_codes=("B03002_001E",),
    ),
    ModelFeature(
        source_table="B03002",
        table_code=None,
        var_name="HISPSHARE",
        description="Hispanic or Latino, any race",
        numerator_codes=("B03002_012E",),
        denominator_codes=("B03002_001E",),
    ),
]
