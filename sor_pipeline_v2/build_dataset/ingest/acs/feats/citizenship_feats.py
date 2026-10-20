"""Citizenship and Residency Status features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import B05003I, B29001
from build_dataset.ingest.declarations.denominators import HISPANIC_ADULTS
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
    SumFeature,
)

# Referenced beyond its own declaration (TURNOUT's denominator, the manifest's
# NOT_PREDICTORS), so the name is spelled exactly once.
VOTINGAGEPOP = "VOTINGAGEPOP"

CITIZENSHIP_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ACS",
        var_name="HISPADULTNATURALIZED",
        display_name="Hispanic adult naturalized citizens",
        description="Share of Hispanic adults (18+) who are naturalized U.S. citizens",
        variable_computer=FractionalShare(
            numerator_codes=[
                B05003I.MALE_18_YEARS_AND_OVER_FOREIGN_BORN_NATURALIZED_U_S_CITIZEN,
                B05003I.FEMALE_18_YEARS_AND_OVER_FOREIGN_BORN_NATURALIZED_U_S_CITIZEN,
            ],
            denominator_codes=HISPANIC_ADULTS,
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPADULTNONCITIZEN",
        display_name="Hispanic adult noncitizens",
        description="Share of Hispanic adults (18+) who are not U.S. citizens",
        variable_computer=FractionalShare(
            numerator_codes=[
                B05003I.MALE_18_YEARS_AND_OVER_FOREIGN_BORN_NOT_A_U_S_CITIZEN,
                B05003I.FEMALE_18_YEARS_AND_OVER_FOREIGN_BORN_NOT_A_U_S_CITIZEN,
            ],
            denominator_codes=HISPANIC_ADULTS,
        ),
    ),
    # A raw COUNT, not a share: the clean stage consumes it as the denominator
    # of TURNOUT (election_feats), the only place it is used. Citizens only --
    # B29001's universe excludes non-citizen adults, so in immigrant-heavy
    # counties this is well below the full 18+ population.
    ModelVariable(
        source="ACS",
        var_name=VOTINGAGEPOP,
        display_name="Citizen voting-age population",
        description="Citizen voting-age population (citizens 18 years and over)",
        variable_computer=SumFeature(codes=[B29001.TOTAL]),
        role="context",
    ),
]
