"""Mobility and Time in the U.S. features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import (
    B03001,
    B05002,
    B05003I,
    B05005,
    B05007,
    B07004I,
)
from build_dataset.ingest.declarations.denominators import (
    FOREIGN_BORN_BY_ENTRY_PERIOD,
    HISPANIC_ADULTS,
    HISPANIC_CHILDREN,
    Denominator,
)
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    LogGrowth,
    ModelVariable,
)

# The codes the growth features (HISPGROWTH and FBGROWTH below) compare
# across ACS vintages: the Hispanic population and the foreign-born population.
PRIOR_CODES: tuple[str, ...] = ("B03001_003E", "B05002_013E")

# The prior-vintage fetch returns the SAME code names as the 2016-2020 fetch
# (both vintages publish B03001_003E, etc.), so its columns are suffixed at
# fetch time to keep the two vintages distinct in the merged dataset. The
# clean stage computes each growth feature from `code` vs `code + PRIOR_SUFFIX`.
PRIOR_SUFFIX = "_PRIOR"

MOBILITY_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ACS",
        var_name="HISPADULTFB",
        display_name="Hispanic adults foreign born",
        description="Share of Hispanic adults (18+) who are foreign born",
        variable_computer=FractionalShare(
            numerator_codes=[
                B05003I.MALE_18_YEARS_AND_OVER_FOREIGN_BORN,
                B05003I.FEMALE_18_YEARS_AND_OVER_FOREIGN_BORN,
            ],
            denominator_codes=HISPANIC_ADULTS,
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPCHILDFB",
        display_name="Hispanic children foreign born",
        description="Share of Hispanic children (under 18) who are foreign born",
        variable_computer=FractionalShare(
            numerator_codes=[
                B05003I.MALE_UNDER_18_YEARS_FOREIGN_BORN,
                B05003I.FEMALE_UNDER_18_YEARS_FOREIGN_BORN,
            ],
            denominator_codes=HISPANIC_CHILDREN,
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="FOREIGNBORNSHARE",
        display_name="Foreign-born share",
        description="Share of the total population that is foreign born",
        variable_computer=FractionalShare(
            numerator_codes=[B05002.FOREIGN_BORN],
            denominator_codes=[Denominator.TOTAL_POPULATION_B05002],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="PRBORNSHARE",
        display_name="Born in Puerto Rico",
        description="Share of the total population born in Puerto Rico (native-born, so invisible "
        "to every foreign-born measure)",
        variable_computer=FractionalShare(
            numerator_codes=[B05002.NATIVE_BORN_OUTSIDE_THE_UNITED_STATES_PUERTO_RICO],
            denominator_codes=[Denominator.TOTAL_POPULATION_B05002],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="FBENTERED2010PLUS",
        display_name="Foreign born entered 2010 or later",
        description="Of the foreign born, the share who entered the U.S. in 2010 or later",
        variable_computer=FractionalShare(
            numerator_codes=[B05005.ENTERED_2010_OR_LATER_FOREIGN_BORN],
            denominator_codes=FOREIGN_BORN_BY_ENTRY_PERIOD,
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="FBENTERED2000S",
        display_name="Foreign born entered 2000-2009",
        description="Of the foreign born, the share who entered the U.S. 2000-2009",
        variable_computer=FractionalShare(
            numerator_codes=[B05005.ENTERED_2000_TO_2009_FOREIGN_BORN],
            denominator_codes=FOREIGN_BORN_BY_ENTRY_PERIOD,
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="FBENTERED1990S",
        display_name="Foreign born entered 1990-1999",
        description="Of the foreign born, the share who entered the U.S. 1990-1999",
        variable_computer=FractionalShare(
            numerator_codes=[B05005.ENTERED_1990_TO_1999_FOREIGN_BORN],
            denominator_codes=FOREIGN_BORN_BY_ENTRY_PERIOD,
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="FBENTEREDPRE1990",
        display_name="Foreign born entered before 1990",
        description="Of the foreign born, the share who entered the U.S. before 1990",
        variable_computer=FractionalShare(
            numerator_codes=[B05005.ENTERED_BEFORE_1990_FOREIGN_BORN],
            denominator_codes=FOREIGN_BORN_BY_ENTRY_PERIOD,
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="LATAMFBENTERED2010PLUS",
        display_name="Latin American foreign born entered 2010 or later",
        description="Of the Latin-American foreign born, the share who entered the U.S. in 2010 or "
        "later",
        variable_computer=FractionalShare(
            numerator_codes=[
                B05007.LATIN_AMERICA_CARIBBEAN_ENTERED_2010_OR_LATER,
                B05007.LATIN_AMERICA_CENTRAL_AMERICA_MEXICO_ENTERED_2010_OR_LATER,
                B05007.LATIN_AMERICA_OTHER_CENTRAL_AMERICA_ENTERED_2010_OR_LATER,
                B05007.LATIN_AMERICA_SOUTH_AMERICA_ENTERED_2010_OR_LATER,
            ],
            denominator_codes=[Denominator.LATIN_AMERICAN_FOREIGN_BORN],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="LATAMFBENTERED2000S",
        display_name="Latin American foreign born entered 2000-2009",
        description="Of the Latin-American foreign born, the share who entered the U.S. 2000-2009",
        variable_computer=FractionalShare(
            numerator_codes=[
                B05007.LATIN_AMERICA_CARIBBEAN_ENTERED_2000_TO_2009,
                B05007.LATIN_AMERICA_CENTRAL_AMERICA_MEXICO_ENTERED_2000_TO_2009,
                B05007.LATIN_AMERICA_OTHER_CENTRAL_AMERICA_ENTERED_2000_TO_2009,
                B05007.LATIN_AMERICA_SOUTH_AMERICA_ENTERED_2000_TO_2009,
            ],
            denominator_codes=[Denominator.LATIN_AMERICAN_FOREIGN_BORN],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="LATAMFBENTERED1990S",
        display_name="Latin American foreign born entered 1990-1999",
        description="Of the Latin-American foreign born, the share who entered the U.S. 1990-1999",
        variable_computer=FractionalShare(
            numerator_codes=[
                B05007.LATIN_AMERICA_CARIBBEAN_ENTERED_1990_TO_1999,
                B05007.LATIN_AMERICA_CENTRAL_AMERICA_MEXICO_ENTERED_1990_TO_1999,
                B05007.LATIN_AMERICA_OTHER_CENTRAL_AMERICA_ENTERED_1990_TO_1999,
                B05007.LATIN_AMERICA_SOUTH_AMERICA_ENTERED_1990_TO_1999,
            ],
            denominator_codes=[Denominator.LATIN_AMERICAN_FOREIGN_BORN],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="LATAMFBENTEREDPRE1990",
        display_name="Latin American foreign born entered before 1990",
        description="Of the Latin-American foreign born, the share who entered the U.S. before 1990",
        variable_computer=FractionalShare(
            numerator_codes=[
                B05007.LATIN_AMERICA_CARIBBEAN_ENTERED_BEFORE_1990,
                B05007.LATIN_AMERICA_CENTRAL_AMERICA_MEXICO_ENTERED_BEFORE_1990,
                B05007.LATIN_AMERICA_OTHER_CENTRAL_AMERICA_ENTERED_BEFORE_1990,
                B05007.LATIN_AMERICA_SOUTH_AMERICA_ENTERED_BEFORE_1990,
            ],
            denominator_codes=[Denominator.LATIN_AMERICAN_FOREIGN_BORN],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPMOVEDWITHINCOUNTY",
        display_name="Hispanic moved within county",
        description="Moved within the same county in the past year",
        variable_computer=FractionalShare(
            numerator_codes=[B07004I.MOVED_WITHIN_SAME_COUNTY],
            denominator_codes=[Denominator.HISPANIC_1_AND_OVER],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPMOVEDDIFFCOUNTY",
        display_name="Hispanic moved from another county",
        description="Moved from a different county in the same state",
        variable_computer=FractionalShare(
            numerator_codes=[B07004I.MOVED_FROM_DIFFERENT_COUNTY_WITHIN_SAME_STATE],
            denominator_codes=[Denominator.HISPANIC_1_AND_OVER],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPMOVEDDIFFSTATE",
        display_name="Hispanic moved from another state",
        description="Moved from a different state",
        variable_computer=FractionalShare(
            numerator_codes=[B07004I.MOVED_FROM_DIFFERENT_STATE],
            denominator_codes=[Denominator.HISPANIC_1_AND_OVER],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPMOVEDABROAD",
        display_name="Hispanic moved from abroad",
        description="Moved from abroad in the past year",
        variable_computer=FractionalShare(
            numerator_codes=[B07004I.MOVED_FROM_ABROAD],
            denominator_codes=[Denominator.HISPANIC_1_AND_OVER],
        ),
    ),
    # Prior-vintage growth features: population change, 2011-2015 -> 2016-2020.
    # Each compares one code across two ACS vintages as a log ratio,
    # log(2020 + 1) - log(2015 + 1), reading `code` vs `code + PRIOR_SUFFIX`
    # (declared above).
    #
    # Log ratio, not percent change: for a random forest the two are
    # interchangeable (monotone transforms produce identical trees), but percent
    # change is undefined in the 11 counties with no Hispanic residents in 2015
    # and reaches 3,738% at the top. The log ratio is defined everywhere;
    # 0.13 is the national median, roughly 14% growth. Distinguishes established
    # Hispanic communities from new destinations, a concept none of the
    # point-in-time features capture.
    ModelVariable(
        source="ACS",
        var_name="HISPGROWTH",
        display_name="Hispanic population growth",
        description="Change in the county Hispanic population (B03001_003E) "
        "from the 2011-2015 ACS to the 2016-2020 ACS, as a log ratio: "
        "log(2020 + 1) - log(2015 + 1). Positive means growth.",
        variable_computer=LogGrowth(
            current_code=B03001.HISPANIC_OR_LATINO,
            prior_code=B03001.HISPANIC_OR_LATINO + PRIOR_SUFFIX,
        ),
    ),
    # Measures something HISPGROWTH does not: Spearman between the two is only
    # +0.27. Three times as many counties are losing foreign-born residents
    # (1,332) as are losing Hispanic residents (418), because Hispanic growth is
    # increasingly US-born -- a county can gain Hispanics while losing immigrants.
    ModelVariable(
        source="ACS",
        var_name="FBGROWTH",
        display_name="Foreign-born population growth",
        description="Change in the county foreign-born population (B05002_013E) "
        "from the 2011-2015 ACS to the 2016-2020 ACS, as a log ratio. "
        "Positive means growth.",
        variable_computer=LogGrowth(
            current_code=B05002.FOREIGN_BORN,
            prior_code=B05002.FOREIGN_BORN + PRIOR_SUFFIX,
        ),
    ),
]
