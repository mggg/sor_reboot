"""Mobility and Time in the U.S. features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.feature_utils import ModelFeature

MOBILITY_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="B05003I",
        table_code=None,
        var_name="HISPADULTFB",
        description="Share of Hispanic adults (18+) who are foreign born",
        numerator_codes=("B05003I_010E", "B05003I_021E"),
        denominator_codes=("B05003I_008E", "B05003I_019E"),
    ),
    ModelFeature(
        source_table="B05003I",
        table_code=None,
        var_name="HISPCHILDFB",
        description="Share of Hispanic children (under 18) who are foreign born",
        numerator_codes=("B05003I_005E", "B05003I_016E"),
        denominator_codes=("B05003I_003E", "B05003I_014E"),
    ),
    ModelFeature(
        source_table="B05002",
        table_code=None,
        var_name="FOREIGNBORNSHARE",
        description="Share of the total population that is foreign born",
        numerator_codes=("B05002_013E",),
        denominator_codes=("B05002_001E",),
    ),
    ModelFeature(
        source_table="B05002",
        table_code=None,
        var_name="PRBORNSHARE",
        description="Share of the total population born in Puerto Rico (native-born, so invisible "
        "to every foreign-born measure)",
        numerator_codes=("B05002_010E",),
        denominator_codes=("B05002_001E",),
    ),
    ModelFeature(
        source_table="B05005",
        table_code=None,
        var_name="FBENTERED2010PLUS",
        description="Of the foreign born, the share who entered the U.S. in 2010 or later",
        numerator_codes=("B05005_004E",),
        denominator_codes=("B05005_004E", "B05005_009E", "B05005_014E", "B05005_019E"),
    ),
    ModelFeature(
        source_table="B05005",
        table_code=None,
        var_name="FBENTERED2000S",
        description="Of the foreign born, the share who entered the U.S. 2000-2009",
        numerator_codes=("B05005_009E",),
        denominator_codes=("B05005_004E", "B05005_009E", "B05005_014E", "B05005_019E"),
    ),
    ModelFeature(
        source_table="B05005",
        table_code=None,
        var_name="FBENTERED1990S",
        description="Of the foreign born, the share who entered the U.S. 1990-1999",
        numerator_codes=("B05005_014E",),
        denominator_codes=("B05005_004E", "B05005_009E", "B05005_014E", "B05005_019E"),
    ),
    ModelFeature(
        source_table="B05005",
        table_code=None,
        var_name="FBENTEREDPRE1990",
        description="Of the foreign born, the share who entered the U.S. before 1990",
        numerator_codes=("B05005_019E",),
        denominator_codes=("B05005_004E", "B05005_009E", "B05005_014E", "B05005_019E"),
    ),
    ModelFeature(
        source_table="B05007",
        table_code=None,
        var_name="LATAMFBENTERED2010PLUS",
        description="Of the Latin-American foreign born, the share who entered the U.S. in 2010 or "
        "later",
        numerator_codes=("B05007_042E", "B05007_056E", "B05007_069E", "B05007_082E"),
        denominator_codes=("B05007_040E",),
    ),
    ModelFeature(
        source_table="B05007",
        table_code=None,
        var_name="LATAMFBENTERED2000S",
        description="Of the Latin-American foreign born, the share who entered the U.S. 2000-2009",
        numerator_codes=("B05007_045E", "B05007_059E", "B05007_072E", "B05007_085E"),
        denominator_codes=("B05007_040E",),
    ),
    ModelFeature(
        source_table="B05007",
        table_code=None,
        var_name="LATAMFBENTERED1990S",
        description="Of the Latin-American foreign born, the share who entered the U.S. 1990-1999",
        numerator_codes=("B05007_048E", "B05007_062E", "B05007_075E", "B05007_088E"),
        denominator_codes=("B05007_040E",),
    ),
    ModelFeature(
        source_table="B05007",
        table_code=None,
        var_name="LATAMFBENTEREDPRE1990",
        description="Of the Latin-American foreign born, the share who entered the U.S. before 1990",
        numerator_codes=("B05007_051E", "B05007_065E", "B05007_078E", "B05007_091E"),
        denominator_codes=("B05007_040E",),
    ),
    ModelFeature(
        source_table="B07004I",
        table_code=None,
        var_name="HISPMOVEDWITHINCOUNTY",
        description="Moved within the same county in the past year",
        numerator_codes=("B07004I_003E",),
        denominator_codes=("B07004I_001E",),
    ),
    ModelFeature(
        source_table="B07004I",
        table_code=None,
        var_name="HISPMOVEDDIFFCOUNTY",
        description="Moved from a different county in the same state",
        numerator_codes=("B07004I_004E",),
        denominator_codes=("B07004I_001E",),
    ),
    ModelFeature(
        source_table="B07004I",
        table_code=None,
        var_name="HISPMOVEDDIFFSTATE",
        description="Moved from a different state",
        numerator_codes=("B07004I_005E",),
        denominator_codes=("B07004I_001E",),
    ),
    ModelFeature(
        source_table="B07004I",
        table_code=None,
        var_name="HISPMOVEDABROAD",
        description="Moved from abroad in the past year",
        numerator_codes=("B07004I_006E",),
        denominator_codes=("B07004I_001E",),
    ),
    # Prior-vintage growth features: population change, 2011-2015 -> 2016-2020,
    # custom: each compares one code across two ACS vintages as a log ratio,
    # log(2020 + 1) - log(2015 + 1), computed in the derive stage from
    # `code` vs `code + PRIOR_SUFFIX` (declared below).
    #
    # Log ratio, not percent change: for a random forest the two are
    # interchangeable (monotone transforms produce identical trees), but percent
    # change is undefined in the 11 counties with no Hispanic residents in 2015
    # and reaches 3,738% at the top. The log ratio is defined everywhere;
    # 0.13 is the national median, roughly 14% growth. Distinguishes established
    # Hispanic communities from new destinations, a concept none of the
    # point-in-time features capture.
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="HISPGROWTH",
        description="Change in the county Hispanic population (B03001_003E) "
        "from the 2011-2015 ACS to the 2016-2020 ACS, as a log ratio: "
        "log(2020 + 1) - log(2015 + 1). Positive means growth.",
        custom=True,
    ),
    # Measures something HISPGROWTH does not: Spearman between the two is only
    # +0.27. Three times as many counties are losing foreign-born residents
    # (1,332) as are losing Hispanic residents (418), because Hispanic growth is
    # increasingly US-born -- a county can gain Hispanics while losing immigrants.
    ModelFeature(
        source_table="B05002",
        table_code=None,
        var_name="FBGROWTH",
        description="Change in the county foreign-born population (B05002_013E) "
        "from the 2011-2015 ACS to the 2016-2020 ACS, as a log ratio. "
        "Positive means growth.",
        custom=True,
    ),
]

# The codes the growth features (HISPGROWTH and FBGROWTH above) compare
# across ACS vintages: the Hispanic population and the foreign-born population.
PRIOR_CODES: tuple[str, ...] = ("B03001_003E", "B05002_013E")

# The prior-vintage fetch returns the SAME code names as the 2016-2020 fetch
# (both vintages publish B03001_003E, etc.), so its columns are suffixed at
# fetch time to keep the two vintages distinct in the merged dataset. The
# clean stage computes each growth feature from `code` vs `code + PRIOR_SUFFIX`.
PRIOR_SUFFIX = "_PRIOR"
