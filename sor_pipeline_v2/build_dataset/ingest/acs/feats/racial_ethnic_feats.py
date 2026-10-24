"""Racial and Ethnic Composition features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import B03002
from build_dataset.ingest.declarations.denominators import Denominator
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
)

RACIAL_ETHNIC_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ACS",
        var_name="NONHISPANICWHITESHARE",
        display_name="Non-Hispanic White share",
        description="Non-Hispanic White alone",
        variable_computer=FractionalShare(
            numerator_codes=[B03002.NOT_HISPANIC_OR_LATINO_WHITE_ALONE],
            denominator_codes=[Denominator.TOTAL_POPULATION_B03002],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="NONHISPANICBLACKSHARE",
        display_name="Non-Hispanic Black share",
        description="Non-Hispanic Black or African American alone",
        variable_computer=FractionalShare(
            numerator_codes=[
                B03002.NOT_HISPANIC_OR_LATINO_BLACK_OR_AFRICAN_AMERICAN_ALONE
            ],
            denominator_codes=[Denominator.TOTAL_POPULATION_B03002],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="NONHISPANICAIANSHARE",
        display_name="Non-Hispanic AIAN share",
        description="Non-Hispanic American Indian and Alaska Native alone",
        variable_computer=FractionalShare(
            numerator_codes=[
                B03002.NOT_HISPANIC_OR_LATINO_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ALONE
            ],
            denominator_codes=[Denominator.TOTAL_POPULATION_B03002],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="NONHISPANICASIANSHARE",
        display_name="Non-Hispanic Asian share",
        description="Non-Hispanic Asian alone",
        variable_computer=FractionalShare(
            numerator_codes=[B03002.NOT_HISPANIC_OR_LATINO_ASIAN_ALONE],
            denominator_codes=[Denominator.TOTAL_POPULATION_B03002],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="NONHISPANICMULTISHARE",
        display_name="Non-Hispanic multiracial share",
        description="Non-Hispanic, two or more races -- the unit's non-Hispanic propensity for "
        "multiracial reporting",
        variable_computer=FractionalShare(
            numerator_codes=[B03002.NOT_HISPANIC_OR_LATINO_TWO_OR_MORE_RACES],
            denominator_codes=[Denominator.TOTAL_POPULATION_B03002],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPSHARE",
        display_name="Hispanic share",
        description="Hispanic or Latino, any race",
        variable_computer=FractionalShare(
            numerator_codes=[B03002.HISPANIC_OR_LATINO],
            denominator_codes=[Denominator.TOTAL_POPULATION_B03002],
        ),
    ),
]
