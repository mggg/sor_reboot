"""English names for every share denominator: the universe each share divides by.

Members are StrEnum values, so each IS its census code string and drops
straight into a computer's code list. Where the census publishes "the same"
universe in several subject tables (with genuinely different counts), the
member name carries its table code: a share must divide by its own table's
total, and the suffix says whose count it is.

The list constants below the enum are the composite denominators -- universes
the census only publishes as several lines to be summed.
"""

from enum import StrEnum


class Denominator(StrEnum):
    # Total and Hispanic populations, per table
    HISPANIC_POPULATION_B03001 = "B03001_003E"
    HISPANIC_POPULATION_B01001I = "B01001I_001E"
    TOTAL_POPULATION_B03002 = "B03002_001E"
    TOTAL_POPULATION_B05002 = "B05002_001E"
    TOTAL_POPULATION_DHC = "DHC_P2_001N"

    # Hispanic age-restricted universes
    HISPANIC_5_AND_OVER_B16006 = "B16006_001E"
    HISPANIC_5_AND_OVER_B16005I = "B16005I_001E"
    HISPANIC_1_AND_OVER = "B07004I_001E"
    HISPANIC_16_AND_OVER = "C23002I_001E"
    HISPANIC_25_AND_OVER = "C15002I_001E"

    # Household and housing universes
    HISPANIC_HOUSEHOLDS_B11001I = "B11001I_001E"
    HISPANIC_HOUSEHOLDS_B22005I = "B22005I_001E"
    HISPANIC_OCCUPIED_UNITS_B25003I = "B25003I_001E"
    HISPANIC_OCCUPIED_UNITS_B25014I = "B25014I_001E"
    HISPANIC_IN_HOUSEHOLDS = "B28009I_001E"
    ALL_HOUSEHOLDS = "B11001_001E"

    # Other universes
    HISPANIC_POVERTY_UNIVERSE = "B17001I_001E"
    HISPANIC_CIVILIAN_EMPLOYED = "C24010I_001E"
    CIVILIAN_EMPLOYED = "C24030_001E"
    FOREIGN_BORN = "B05002_013E"
    LATIN_AMERICAN_FOREIGN_BORN = "B05007_040E"


# Composite denominators: summed at compute time.
HISPANIC_ADULTS: list[str] = ["B05003I_008E", "B05003I_019E"]  # male + female 18+
HISPANIC_CHILDREN: list[str] = ["B05003I_003E", "B05003I_014E"]  # male + female <18
HISPANIC_LABOR_FORCE: list[str] = [
    "C23002I_004E",
    "C23002I_011E",
    "C23002I_017E",
    "C23002I_024E",
]
FOREIGN_BORN_BY_ENTRY_PERIOD: list[str] = [
    "B05005_004E",
    "B05005_009E",
    "B05005_014E",
    "B05005_019E",
]
HISPANIC_WORKING_AGE: list[str] = [  # 18-64, male then female lines of B01001I
    "B01001I_007E",
    "B01001I_008E",
    "B01001I_009E",
    "B01001I_010E",
    "B01001I_011E",
    "B01001I_012E",
    "B01001I_013E",
    "B01001I_022E",
    "B01001I_023E",
    "B01001I_024E",
    "B01001I_025E",
    "B01001I_026E",
    "B01001I_027E",
    "B01001I_028E",
]
