"""Income and Affluence features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import (
    B17001I,
    B19301I,
    B22005I,
    B25003I,
    B25014I,
    B28009I,
)
from build_dataset.ingest.declarations.denominators import Denominator
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
    SumFeature,
)

INCOME_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ACS",
        var_name="HISPPERCAPINCOME",
        display_name="Hispanic per capita income",
        description="Per capita income, Hispanic population (2020 dollars)",
        variable_computer=SumFeature(
            codes=[
                B19301I.PER_CAPITA_INCOME_IN_THE_PAST_12_MONTHS_IN_2020_INFLATION_ADJUSTED_DOLLARS
            ]
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPPOVERTY",
        display_name="Hispanic poverty rate",
        description="Income in the past 12 months below the poverty level",
        variable_computer=FractionalShare(
            numerator_codes=[B17001I.INCOME_IN_THE_PAST_12_MONTHS_BELOW_POVERTY_LEVEL],
            denominator_codes=[Denominator.HISPANIC_POVERTY_UNIVERSE],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPSNAP",
        display_name="Hispanic SNAP receipt",
        description="Received SNAP/Food Stamps in the past 12 months",
        variable_computer=FractionalShare(
            numerator_codes=[
                B22005I.HOUSEHOLD_RECEIVED_FOOD_STAMPS_SNAP_IN_THE_PAST_12_MONTHS
            ],
            denominator_codes=[Denominator.HISPANIC_HOUSEHOLDS_B22005I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPOWNEROCC",
        display_name="Hispanic owner-occupied housing",
        description="Owner-occupied (renter-occupied is the exact complement)",
        variable_computer=FractionalShare(
            numerator_codes=[B25003I.OWNER_OCCUPIED],
            denominator_codes=[Denominator.HISPANIC_OCCUPIED_UNITS_B25003I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPCROWDING",
        display_name="Hispanic crowded housing",
        description="Crowded housing: 1.01 or more occupants per room",
        variable_computer=FractionalShare(
            numerator_codes=[B25014I.OCCUPANTS_PER_ROOM_1_01_OR_MORE],
            denominator_codes=[Denominator.HISPANIC_OCCUPIED_UNITS_B25014I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPBROADBAND",
        display_name="Hispanic broadband access",
        description="Has a computer with a broadband internet subscription",
        variable_computer=FractionalShare(
            numerator_codes=[
                B28009I.HAS_A_COMPUTER_WITH_A_BROADBAND_INTERNET_SUBSCRIPTION
            ],
            denominator_codes=[Denominator.HISPANIC_IN_HOUSEHOLDS],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPCOMPUTERNOBROADBAND",
        display_name="Hispanic computer without broadband",
        description="Has a computer but no broadband (dial-up only, or no subscription)",
        variable_computer=FractionalShare(
            numerator_codes=[
                B28009I.HAS_A_COMPUTER_WITH_DIAL_UP_INTERNET_SUBSCRIPTION_ALONE,
                B28009I.HAS_A_COMPUTER_WITHOUT_AN_INTERNET_SUBSCRIPTION,
            ],
            denominator_codes=[Denominator.HISPANIC_IN_HOUSEHOLDS],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPNOCOMPUTER",
        display_name="Hispanic no computer",
        description="No computer in the household",
        variable_computer=FractionalShare(
            numerator_codes=[B28009I.NO_COMPUTER],
            denominator_codes=[Denominator.HISPANIC_IN_HOUSEHOLDS],
        ),
    ),
]
