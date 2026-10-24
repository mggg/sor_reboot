"""Household Structure (age, marriage, sex) features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import (
    B01001I,
    B01002I,
    B11001,
    B11001I,
)
from build_dataset.ingest.declarations.denominators import (
    HISPANIC_WORKING_AGE,
    Denominator,
)
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
    SumFeature,
)

HOUSEHOLD_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ACS",
        var_name="HISPMEDAGE",
        display_name="Hispanic median age",
        description="Median age of the Hispanic population",
        variable_computer=SumFeature(codes=[B01002I.MEDIAN_AGE]),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPUNDER18",
        display_name="Hispanic under 18",
        description="Under 18 years",
        variable_computer=FractionalShare(
            numerator_codes=[
                B01001I.MALE_UNDER_5_YEARS,
                B01001I.MALE_5_TO_9_YEARS,
                B01001I.MALE_10_TO_14_YEARS,
                B01001I.MALE_15_TO_17_YEARS,
                B01001I.FEMALE_UNDER_5_YEARS,
                B01001I.FEMALE_5_TO_9_YEARS,
                B01001I.FEMALE_10_TO_14_YEARS,
                B01001I.FEMALE_15_TO_17_YEARS,
            ],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B01001I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISP18TO34",
        display_name="Hispanic 18 to 34",
        description="18 to 34 years",
        variable_computer=FractionalShare(
            numerator_codes=[
                B01001I.MALE_18_AND_19_YEARS,
                B01001I.MALE_20_TO_24_YEARS,
                B01001I.MALE_25_TO_29_YEARS,
                B01001I.MALE_30_TO_34_YEARS,
                B01001I.FEMALE_18_AND_19_YEARS,
                B01001I.FEMALE_20_TO_24_YEARS,
                B01001I.FEMALE_25_TO_29_YEARS,
                B01001I.FEMALE_30_TO_34_YEARS,
            ],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B01001I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISP35TO64",
        display_name="Hispanic 35 to 64",
        description="35 to 64 years",
        variable_computer=FractionalShare(
            numerator_codes=[
                B01001I.MALE_35_TO_44_YEARS,
                B01001I.MALE_45_TO_54_YEARS,
                B01001I.MALE_55_TO_64_YEARS,
                B01001I.FEMALE_35_TO_44_YEARS,
                B01001I.FEMALE_45_TO_54_YEARS,
                B01001I.FEMALE_55_TO_64_YEARS,
            ],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B01001I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISP65PLUS",
        display_name="Hispanic 65 and over",
        description="65 years and over",
        variable_computer=FractionalShare(
            numerator_codes=[
                B01001I.MALE_65_TO_74_YEARS,
                B01001I.MALE_75_TO_84_YEARS,
                B01001I.MALE_85_YEARS_AND_OVER,
                B01001I.FEMALE_65_TO_74_YEARS,
                B01001I.FEMALE_75_TO_84_YEARS,
                B01001I.FEMALE_85_YEARS_AND_OVER,
            ],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B01001I],
        ),
    ),
    # Formerly a clean-stage derived feature: the finished HISPUNDER18 share
    # divided by (HISP18TO34 + HISP35TO64). All three are shares of the same
    # B01001I total, so the totals cancel and the ratio is a plain sum-over-sum
    # of that table's lines -- declared here like any other feature. It is a
    # RATIO (children per working-age adult, can exceed 1), not a 0-to-1 share.
    ModelVariable(
        source="ACS",
        var_name="HISPYOUTHDEP",
        display_name="Hispanic youth dependency ratio",
        description="Youth dependency ratio: Hispanic children (under 18) per "
        "Hispanic working-age adult (18 to 64)",
        variable_computer=FractionalShare(
            numerator_codes=[
                B01001I.MALE_UNDER_5_YEARS,
                B01001I.MALE_5_TO_9_YEARS,
                B01001I.MALE_10_TO_14_YEARS,
                B01001I.MALE_15_TO_17_YEARS,
                B01001I.FEMALE_UNDER_5_YEARS,
                B01001I.FEMALE_5_TO_9_YEARS,
                B01001I.FEMALE_10_TO_14_YEARS,
                B01001I.FEMALE_15_TO_17_YEARS,
            ],
            denominator_codes=HISPANIC_WORKING_AGE,
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPHHMARRIED",
        display_name="Hispanic married-couple households",
        description="Married-couple family households",
        variable_computer=FractionalShare(
            numerator_codes=[B11001I.FAMILY_HOUSEHOLDS_MARRIED_COUPLE_FAMILY],
            denominator_codes=[Denominator.HISPANIC_HOUSEHOLDS_B11001I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPHHMALENOSPOUSE",
        display_name="Hispanic male householder, no spouse",
        description="Male householder, no spouse present",
        variable_computer=FractionalShare(
            numerator_codes=[
                B11001I.FAMILY_HOUSEHOLDS_OTHER_FAMILY_MALE_HOUSEHOLDER_NO_SPOUSE_PRESENT
            ],
            denominator_codes=[Denominator.HISPANIC_HOUSEHOLDS_B11001I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPHHFEMALENOSPOUSE",
        display_name="Hispanic female householder, no spouse",
        description="Female householder, no spouse present",
        variable_computer=FractionalShare(
            numerator_codes=[
                B11001I.FAMILY_HOUSEHOLDS_OTHER_FAMILY_FEMALE_HOUSEHOLDER_NO_SPOUSE_PRESENT
            ],
            denominator_codes=[Denominator.HISPANIC_HOUSEHOLDS_B11001I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPHHALONE",
        display_name="Hispanic householders living alone",
        description="Householder living alone",
        variable_computer=FractionalShare(
            numerator_codes=[B11001I.NONFAMILY_HOUSEHOLDS_HOUSEHOLDER_LIVING_ALONE],
            denominator_codes=[Denominator.HISPANIC_HOUSEHOLDS_B11001I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HHMARRIEDALL",
        display_name="Married-couple share of all households",
        description="Married-couple family households as a share of every "
        "household in the unit, Hispanic or not -- the counterpart to "
        "HISPHHMARRIED, which is computed within Hispanic households",
        variable_computer=FractionalShare(
            numerator_codes=[B11001.FAMILY_HOUSEHOLDS_MARRIED_COUPLE_FAMILY],
            denominator_codes=[Denominator.ALL_HOUSEHOLDS],
        ),
    ),
]
