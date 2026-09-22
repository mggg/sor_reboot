"""National Origin and Background features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.feature_utils import ModelFeature

NATIONAL_ORIGIN_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="MEXICANORIGIN",
        description="Mexican origin. Top-level category; 58% of US Hispanics.",
        numerator_codes=("B03001_004E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="PUERTORICANORIGIN",
        description="Puerto Rican origin. Top-level category.",
        numerator_codes=("B03001_005E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="CUBANORIGIN",
        description="Cuban origin. Top-level category.",
        numerator_codes=("B03001_006E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="DOMINICANORIGIN",
        description="Dominican (Dominican Republic) origin. Top-level category.",
        numerator_codes=("B03001_007E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="CENTRALAMORIGIN",
        description="Central American origin, TOTAL across all countries. Contains the Guatemalan, "
        "Honduran and Salvadoran features below, plus Costa Rican, Nicaraguan and "
        "Panamanian, which are not modeled.",
        numerator_codes=("B03001_008E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="GUATEMALANORIGIN",
        description="Guatemalan origin. A subset of CENTRALAMORIGIN, not additional to it.",
        numerator_codes=("B03001_010E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="HONDURANORIGIN",
        description="Honduran origin. A subset of CENTRALAMORIGIN, not additional to it.",
        numerator_codes=("B03001_011E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="SALVADORANORIGIN",
        description="Salvadoran origin. A subset of CENTRALAMORIGIN, not additional to it.",
        numerator_codes=("B03001_014E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="SOUTHAMORIGIN",
        description="South American origin, TOTAL across all countries. Contains the Colombian, "
        "Ecuadorian, Peruvian and Venezuelan features below, plus six smaller "
        "nationalities that are not modeled.",
        numerator_codes=("B03001_016E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="COLOMBIANORIGIN",
        description="Colombian origin. A subset of SOUTHAMORIGIN, not additional to it.",
        numerator_codes=("B03001_020E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="ECUADORIANORIGIN",
        description="Ecuadorian origin. A subset of SOUTHAMORIGIN, not additional to it.",
        numerator_codes=("B03001_021E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="PERUVIANORIGIN",
        description="Peruvian origin. A subset of SOUTHAMORIGIN, not additional to it.",
        numerator_codes=("B03001_023E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="VENEZUELANORIGIN",
        description="Venezuelan origin. A subset of SOUTHAMORIGIN, not additional to it.",
        numerator_codes=("B03001_025E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="OTHERORIGINTOTAL",
        description="Other Hispanic or Latino, TOTAL: everyone whose reported origin is not "
        "Mexican, Puerto Rican, Cuban, Dominican, Central American or South American. "
        "5.5% of US Hispanics. Contains the two features below.",
        numerator_codes=("B03001_027E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="SPANIARDORIGIN",
        description="Spaniard (origin in Spain). A subset of OTHERORIGINTOTAL.",
        numerator_codes=("B03001_028E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B03001",
        table_code=None,
        var_name="HISPORIGINUNSPECIFIED",
        description="Reported a Hispanic or Latino identity but no specific national origin: "
        'write-ins such as "Hispanic", "Latino" or "Latin American", plus origins '
        "too small for the Census to tabulate separately. A subset of OTHERORIGINTOTAL, "
        "and 57% of it. 1.95 million people, 3.1% of US Hispanics.",
        numerator_codes=("B03001_031E",),
        denominator_codes=("B03001_003E",),
    ),
    ModelFeature(
        source_table="B05002",
        table_code=None,
        var_name="FBLATAMSHARE",
        description="Of the foreign born, the share born in Latin America (naturalized plus "
        "non-citizen)",
        numerator_codes=("B05002_019E", "B05002_026E"),
        denominator_codes=("B05002_013E",),
    ),
]
