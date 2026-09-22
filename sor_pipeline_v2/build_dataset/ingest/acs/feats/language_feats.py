"""Language features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.feature_utils import ModelFeature

LANGUAGE_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="B16006",
        table_code=None,
        var_name="HISPENGONLY",
        description="Hispanics who speak only English at home",
        numerator_codes=("B16006_002E",),
        denominator_codes=("B16006_001E",),
    ),
    ModelFeature(
        source_table="B16006",
        table_code=None,
        var_name="HISPSPANVERYWELL",
        description='Spanish speakers who report speaking English "very well"',
        numerator_codes=("B16006_004E",),
        denominator_codes=("B16006_001E",),
    ),
    ModelFeature(
        source_table="B16006",
        table_code=None,
        var_name="HISPSPANWELL",
        description='Spanish speakers who report speaking English "well"',
        numerator_codes=("B16006_005E",),
        denominator_codes=("B16006_001E",),
    ),
    ModelFeature(
        source_table="B16006",
        table_code=None,
        var_name="HISPSPANNOTWELL",
        description='Spanish speakers who report speaking English "not well"',
        numerator_codes=("B16006_006E",),
        denominator_codes=("B16006_001E",),
    ),
    ModelFeature(
        source_table="B16006",
        table_code=None,
        var_name="HISPSPANNOTATALL",
        description='Spanish speakers who report speaking English "not at all"',
        numerator_codes=("B16006_007E",),
        denominator_codes=("B16006_001E",),
    ),
    ModelFeature(
        source_table="B16006",
        table_code=None,
        var_name="HISPOTHERLANG",
        description="Hispanics who speak a language other than English or Spanish at home",
        numerator_codes=("B16006_008E",),
        denominator_codes=("B16006_001E",),
    ),
    ModelFeature(
        source_table="B16005I",
        table_code=None,
        var_name="HISPNATIVEENGONLY",
        description="Native-born Hispanics who speak only English at home",
        numerator_codes=("B16005I_003E",),
        denominator_codes=("B16005I_001E",),
    ),
    ModelFeature(
        source_table="B16005I",
        table_code=None,
        var_name="HISPNATIVEOTHERVW",
        description='Native-born Hispanics who speak another language and English "very well"',
        numerator_codes=("B16005I_005E",),
        denominator_codes=("B16005I_001E",),
    ),
    ModelFeature(
        source_table="B16005I",
        table_code=None,
        var_name="HISPNATIVEOTHERLTVW",
        description='Native-born Hispanics who speak another language and English less than "very '
        'well"',
        numerator_codes=("B16005I_006E",),
        denominator_codes=("B16005I_001E",),
    ),
    ModelFeature(
        source_table="B16005I",
        table_code=None,
        var_name="HISPFBENGONLY",
        description="Foreign-born Hispanics who speak only English at home",
        numerator_codes=("B16005I_008E",),
        denominator_codes=("B16005I_001E",),
    ),
    ModelFeature(
        source_table="B16005I",
        table_code=None,
        var_name="HISPFBOTHERVW",
        description='Foreign-born Hispanics who speak another language and English "very well"',
        numerator_codes=("B16005I_010E",),
        denominator_codes=("B16005I_001E",),
    ),
    ModelFeature(
        source_table="B16005I",
        table_code=None,
        var_name="HISPFBOTHERLTVW",
        description='Foreign-born Hispanics who speak another language and English less than "very '
        'well"',
        numerator_codes=("B16005I_011E",),
        denominator_codes=("B16005I_001E",),
    ),
]
