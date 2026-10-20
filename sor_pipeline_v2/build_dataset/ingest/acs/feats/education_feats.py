"""Education features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import C15002I
from build_dataset.ingest.declarations.denominators import Denominator
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
)

EDUCATION_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ACS",
        var_name="HISPEDULTHS",
        display_name="Hispanic less than high school",
        description="Less than a high school diploma",
        variable_computer=FractionalShare(
            numerator_codes=[
                C15002I.MALE_LESS_THAN_HIGH_SCHOOL_DIPLOMA,
                C15002I.FEMALE_LESS_THAN_HIGH_SCHOOL_DIPLOMA,
            ],
            denominator_codes=[Denominator.HISPANIC_25_AND_OVER],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPEDUHS",
        display_name="Hispanic high school graduates",
        description="High school graduate or equivalency",
        variable_computer=FractionalShare(
            numerator_codes=[
                C15002I.MALE_HIGH_SCHOOL_GRADUATE_INCLUDES_EQUIVALENCY,
                C15002I.FEMALE_HIGH_SCHOOL_GRADUATE_INCLUDES_EQUIVALENCY,
            ],
            denominator_codes=[Denominator.HISPANIC_25_AND_OVER],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPEDUSOMECOLL",
        display_name="Hispanic some college",
        description="Some college or an associate's degree",
        variable_computer=FractionalShare(
            numerator_codes=[
                C15002I.MALE_SOME_COLLEGE_OR_ASSOCIATE_S_DEGREE,
                C15002I.FEMALE_SOME_COLLEGE_OR_ASSOCIATE_S_DEGREE,
            ],
            denominator_codes=[Denominator.HISPANIC_25_AND_OVER],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPEDUBAPLUS",
        display_name="Hispanic bachelor's or higher",
        description="Bachelor's degree or higher",
        variable_computer=FractionalShare(
            numerator_codes=[
                C15002I.MALE_BACHELOR_S_DEGREE_OR_HIGHER,
                C15002I.FEMALE_BACHELOR_S_DEGREE_OR_HIGHER,
            ],
            denominator_codes=[Denominator.HISPANIC_25_AND_OVER],
        ),
    ),
]
