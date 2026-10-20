"""What the election source declares: the political-preference features.

The election source is a local CSV loaded whole (no variable-code fetch list
to derive). TURNOUT's denominator is the ACS citizenship feature
VOTINGAGEPOP, so it can only be computed after the ACS join.
"""

from build_dataset.ingest.acs.feats.citizenship_feats import VOTINGAGEPOP
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    LogGrowth,
    ModelVariable,
    SignedLean,
    SumFeature,
)

# The standardized 2020 presidential vote columns. The raw CSVs spell them
# differently per level; election_api renames to these on load, and every
# computation reads them through these constants.
DEM_VOTES = "E_20_PRES_DEM"
REP_VOTES = "E_20_PRES_REP"

# The 2016 counterparts, feeding the vote-growth features. The year lives
# in the name, so no _PRIOR-style suffixing is needed (unlike the ACS
# prior vintage, whose codes collide across years).
DEM_VOTES_2016 = "E_16_PRES_DEM"
REP_VOTES_2016 = "E_16_PRES_REP"

# TURNOUT and NUMBEROFVOTERS sit under the elections group though they measure
# participation and size; only VOTELEAN is preference proper.
ELECTION_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ELECTION",
        var_name="VOTELEAN",
        display_name="Two-party vote lean",
        description="(Republican - Democratic) share of the two-party 2020 "
        "presidential vote; positive = Republican-leaning",
        variable_computer=SignedLean(
            positive_codes=[REP_VOTES], negative_codes=[DEM_VOTES]
        ),
    ),
    ModelVariable(
        source="ELECTION",
        var_name="NUMBEROFVOTERS",
        display_name="Two-party votes cast",
        description="Total two-party 2020 presidential vote (Dem + Rep)",
        variable_computer=SumFeature(codes=[DEM_VOTES, REP_VOTES]),
    ),
    ModelVariable(
        source="ELECTION",
        var_name="TURNOUT",
        display_name="Voter turnout",
        description="Two-party 2020 presidential votes cast per voting-age citizen",
        variable_computer=FractionalShare(
            numerator_codes=[DEM_VOTES, REP_VOTES],
            denominator_codes=[VOTINGAGEPOP],
        ),
    ),
    ModelVariable(
        source="ELECTION",
        var_name="DEMGROWTH",
        display_name="Democratic vote growth",
        description="Log growth of the Democratic presidential vote from "
        "2016 to 2020: log1p(2020 votes) - log1p(2016 votes)",
        variable_computer=LogGrowth(current_code=DEM_VOTES, prior_code=DEM_VOTES_2016),
    ),
    ModelVariable(
        source="ELECTION",
        var_name="REPGROWTH",
        display_name="Republican vote growth",
        description="Log growth of the Republican presidential vote from "
        "2016 to 2020: log1p(2020 votes) - log1p(2016 votes)",
        variable_computer=LogGrowth(current_code=REP_VOTES, prior_code=REP_VOTES_2016),
    ),
]
