"""What the election source declares: the political-preference features.

All three are custom: the election source is a local CSV loaded whole, and
VOTELEAN's (Rep - Dem) / (Rep + Dem) is a difference over a sum, which the
generic sum-over-sum builder cannot express. The computations live in the
derive stage:

  VOTELEAN       = (Rep - Dem) / total two-party vote; positive = Republican
  NUMBEROFVOTERS = Dem + Rep (total two-party vote)
  TURNOUT        = NUMBEROFVOTERS / VOTINGAGEPOP (two-party votes cast per
                   voting-age citizen; the denominator is the ACS citizenship
                   feature, so the two meet only after the ACS join)
"""

from build_dataset.ingest.feature_utils import ModelFeature

# TURNOUT and NUMBEROFVOTERS sit under the elections group though they measure
# participation and size; only VOTELEAN is preference proper.
ELECTION_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="ELECTION",
        table_code=None,
        var_name="VOTELEAN",
        description="(Republican - Democratic) share of the two-party 2020 "
        "presidential vote; positive = Republican-leaning",
        custom=True,
    ),
    ModelFeature(
        source_table="ELECTION",
        table_code=None,
        var_name="NUMBEROFVOTERS",
        description="Total two-party 2020 presidential vote (Dem + Rep)",
        custom=True,
    ),
    ModelFeature(
        source_table="ELECTION",
        table_code=None,
        var_name="TURNOUT",
        description="Two-party 2020 presidential votes cast per voting-age citizen",
        custom=True,
    ),
]
