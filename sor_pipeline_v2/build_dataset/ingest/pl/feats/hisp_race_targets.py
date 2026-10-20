"""What the PL step derives beyond its fetch lists: the study's targets.

The PL file publishes no direct Hispanic-by-race lines for the race
combinations the study needs, so each Hispanic-of-race count is a
subtraction (all-population race count minus its non-Hispanic twin), and
the share targets divide those counts by the total or Hispanic population.
Every variable here reads DERIVED columns -- outputs of the PL fetch
lists' computers -- so these lists must be computed after them, counts
before shares (the derive loop preserves list order).

The dominant-race classification targets (largest, Most_*) are NOT
declared here: their argmax-with-tie-breaking logic fits no computer and
lives in clean_and_derive_pl.add_hisp_dominant_race_choice.
"""

from build_dataset.ingest.declarations.feature_utils import (
    Difference,
    FractionalShare,
    ModelVariable,
)
from build_dataset.ingest.pl.feats.hisp_pop_feats import (
    HISPANIC,
    NONHISPANICSORALONE,
    NONHISPANICWHITEALONE,
    NONHISPANICWHITESOR,
)
from build_dataset.ingest.pl.feats.nonhispanic_white_total_feats import (
    NONHISPANICWHITEALONEORCOMBO,
)
from build_dataset.ingest.pl.feats.total_pop_feats import (
    SORALONE,
    TOTALPOP,
    WHITEALONE,
    WHITESOR,
)
from build_dataset.ingest.pl.feats.white_total_feats import WHITEALONEORCOMBO

# The Hispanic-of-race counts and their complements.
HSOR = "HSOR"
H_N_SOR = "H_N_SOR"
HWHITESOR = "HWHITESOR"
H_N_WHITESOR = "H_N_WHITESOR"
HWHITE = "HWHITE"
H_N_WHITE = "H_N_WHITE"
HWHITEACOMBO = "HWHITEACOMBO"
H_N_WHITEACOMBO = "H_N_WHITEACOMBO"

# The share columns (denominator in the name).
HISP_PCT_OF_TOTAL_POP = "Hisp_Pct_of_Total_Pop"
HISP_SOR_ALONE_PCT_OF_TOTAL_POP = "Hisp_SOR_Alone_Pct_of_Total_Pop"
HISP_WHITE_SOR_PCT_OF_TOTAL_POP = "Hisp_White_SOR_Pct_of_Total_Pop"
HISP_WHITE_ALONE_PCT_OF_TOTAL_POP = "Hisp_White_Alone_Pct_of_Total_Pop"
HISP_WHITE_PCT_OF_TOTAL_POP = "Hisp_White_Pct_of_Total_Pop"
HISP_SOR_ALONE_PCT_OF_HISP_POP = "Hisp_SOR_Alone_Pct_of_Hisp_Pop"
HISP_WHITE_SOR_PCT_OF_HISP_POP = "Hisp_White_SOR_Pct_of_Hisp_Pop"
HISP_WHITE_ALONE_PCT_OF_HISP_POP = "Hisp_White_Alone_Pct_of_Hisp_Pop"
HISP_WHITE_PCT_OF_HISP_POP = "Hisp_White_Pct_of_Hisp_Pop"

# Order matters: each complement reads the count declared just before it.
HISP_RACE_COUNTS: list[ModelVariable] = [
    ModelVariable(
        source="PL",
        var_name=HSOR,
        display_name="Hispanic SOR-alone population",
        description="Hispanic residents who selected Some Other Race alone "
        "(all SOR-alone minus non-Hispanic SOR-alone)",
        variable_computer=Difference(
            minuend_code=SORALONE, subtrahend_code=NONHISPANICSORALONE
        ),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=H_N_SOR,
        display_name="Hispanic non-SOR population",
        description="Hispanic residents who did NOT select Some Other Race alone",
        variable_computer=Difference(minuend_code=HISPANIC, subtrahend_code=HSOR),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=HWHITESOR,
        display_name="Hispanic White-and-SOR population",
        description="Hispanic residents who selected White and Some Other Race "
        "(all White-SOR minus non-Hispanic White-SOR)",
        variable_computer=Difference(
            minuend_code=WHITESOR, subtrahend_code=NONHISPANICWHITESOR
        ),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=H_N_WHITESOR,
        display_name="Hispanic non-White-and-SOR population",
        description="Hispanic residents who did NOT select White and Some Other Race",
        variable_computer=Difference(minuend_code=HISPANIC, subtrahend_code=HWHITESOR),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=HWHITE,
        display_name="Hispanic White-alone population",
        description="Hispanic residents who selected White alone "
        "(all White-alone minus non-Hispanic White-alone)",
        variable_computer=Difference(
            minuend_code=WHITEALONE, subtrahend_code=NONHISPANICWHITEALONE
        ),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=H_N_WHITE,
        display_name="Hispanic non-White-alone population",
        description="Hispanic residents who did NOT select White alone",
        variable_computer=Difference(minuend_code=HISPANIC, subtrahend_code=HWHITE),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=HWHITEACOMBO,
        display_name="Hispanic White alone-or-in-combination population",
        description="Hispanic residents who selected White alone or in any "
        "combination (all minus non-Hispanic)",
        variable_computer=Difference(
            minuend_code=WHITEALONEORCOMBO,
            subtrahend_code=NONHISPANICWHITEALONEORCOMBO,
        ),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=H_N_WHITEACOMBO,
        display_name="Hispanic non-White-in-any-combination population",
        description="Hispanic residents who did NOT select White alone or in "
        "any combination",
        variable_computer=Difference(
            minuend_code=HISPANIC, subtrahend_code=HWHITEACOMBO
        ),
        role="target",
    ),
]

# The of-Hisp family is what the regression arm predicts (role="target");
# the of-Total family is descriptive context, never modeled -- the ACS
# HISPSHARE is the predictor version of the same idea.
HISP_RACE_SHARES: list[ModelVariable] = [
    ModelVariable(
        source="PL",
        var_name=HISP_PCT_OF_TOTAL_POP,
        display_name="Hispanic share of total population",
        description="Hispanic population over total population, decennial",
        variable_computer=FractionalShare(
            numerator_codes=[HISPANIC], denominator_codes=[TOTALPOP]
        ),
        role="context",
    ),
    ModelVariable(
        source="PL",
        var_name=HISP_SOR_ALONE_PCT_OF_TOTAL_POP,
        display_name="Hispanic SOR-alone share of total population",
        description="Hispanic SOR-alone population over total population",
        variable_computer=FractionalShare(
            numerator_codes=[HSOR], denominator_codes=[TOTALPOP]
        ),
        role="context",
    ),
    ModelVariable(
        source="PL",
        var_name=HISP_WHITE_SOR_PCT_OF_TOTAL_POP,
        display_name="Hispanic White-and-SOR share of total population",
        description="Hispanic White-and-SOR population over total population",
        variable_computer=FractionalShare(
            numerator_codes=[HWHITESOR], denominator_codes=[TOTALPOP]
        ),
        role="context",
    ),
    ModelVariable(
        source="PL",
        var_name=HISP_WHITE_ALONE_PCT_OF_TOTAL_POP,
        display_name="Hispanic White-alone share of total population",
        description="Hispanic White-alone population over total population",
        variable_computer=FractionalShare(
            numerator_codes=[HWHITE], denominator_codes=[TOTALPOP]
        ),
        role="context",
    ),
    ModelVariable(
        source="PL",
        var_name=HISP_WHITE_PCT_OF_TOTAL_POP,
        display_name="Hispanic White alone-or-in-combination share of total population",
        description="Hispanic White alone-or-in-combination population over "
        "total population",
        variable_computer=FractionalShare(
            numerator_codes=[HWHITEACOMBO], denominator_codes=[TOTALPOP]
        ),
        role="context",
    ),
    ModelVariable(
        source="PL",
        var_name=HISP_SOR_ALONE_PCT_OF_HISP_POP,
        display_name="SOR-alone share of Hispanic population",
        description="THE OUTCOME: share of Hispanic residents who selected "
        "Some Other Race alone",
        variable_computer=FractionalShare(
            numerator_codes=[HSOR], denominator_codes=[HISPANIC]
        ),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=HISP_WHITE_SOR_PCT_OF_HISP_POP,
        display_name="White-and-SOR share of Hispanic population",
        description="THE OUTCOME: share of Hispanic residents who selected "
        "White and Some Other Race",
        variable_computer=FractionalShare(
            numerator_codes=[HWHITESOR], denominator_codes=[HISPANIC]
        ),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=HISP_WHITE_ALONE_PCT_OF_HISP_POP,
        display_name="White-alone share of Hispanic population",
        description="THE OUTCOME: share of Hispanic residents who selected White alone",
        variable_computer=FractionalShare(
            numerator_codes=[HWHITE], denominator_codes=[HISPANIC]
        ),
        role="target",
    ),
    ModelVariable(
        source="PL",
        var_name=HISP_WHITE_PCT_OF_HISP_POP,
        display_name="White alone-or-in-combination share of Hispanic population",
        description="Share of Hispanic residents who selected White alone or "
        "in any combination",
        variable_computer=FractionalShare(
            numerator_codes=[HWHITEACOMBO], denominator_codes=[HISPANIC]
        ),
        role="target",
    ),
]
