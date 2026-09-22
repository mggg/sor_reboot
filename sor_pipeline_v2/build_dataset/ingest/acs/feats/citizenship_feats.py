"""Citizenship and Residency Status features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.feature_utils import ModelFeature

CITIZENSHIP_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="B05003I",
        table_code=None,
        var_name="HISPADULTNATURALIZED",
        description="Share of Hispanic adults (18+) who are naturalized U.S. citizens",
        numerator_codes=("B05003I_011E", "B05003I_022E"),
        denominator_codes=("B05003I_008E", "B05003I_019E"),
    ),
    ModelFeature(
        source_table="B05003I",
        table_code=None,
        var_name="HISPADULTNONCITIZEN",
        description="Share of Hispanic adults (18+) who are not U.S. citizens",
        numerator_codes=("B05003I_012E", "B05003I_023E"),
        denominator_codes=("B05003I_008E", "B05003I_019E"),
    ),
    # A raw COUNT, not a share: the clean stage consumes it as the denominator
    # of TURNOUT (election_feats), the only place it is used. Citizens only --
    # B29001's universe excludes non-citizen adults, so in immigrant-heavy
    # counties this is well below the full 18+ population.
    ModelFeature(
        source_table="B29001",
        table_code="B29001_001E",
        var_name="VOTINGAGEPOP",
        description="Citizen voting-age population (citizens 18 years and over)",
        numerator_codes=("B29001_001E",),
        denominator_codes=(),
    ),
]
