"""Education features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.feature_utils import ModelFeature

EDUCATION_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="C15002I",
        table_code=None,
        var_name="HISPEDULTHS",
        description="Less than a high school diploma",
        numerator_codes=("C15002I_003E", "C15002I_008E"),
        denominator_codes=("C15002I_001E",),
    ),
    ModelFeature(
        source_table="C15002I",
        table_code=None,
        var_name="HISPEDUHS",
        description="High school graduate or equivalency",
        numerator_codes=("C15002I_004E", "C15002I_009E"),
        denominator_codes=("C15002I_001E",),
    ),
    ModelFeature(
        source_table="C15002I",
        table_code=None,
        var_name="HISPEDUSOMECOLL",
        description="Some college or an associate's degree",
        numerator_codes=("C15002I_005E", "C15002I_010E"),
        denominator_codes=("C15002I_001E",),
    ),
    ModelFeature(
        source_table="C15002I",
        table_code=None,
        var_name="HISPEDUBAPLUS",
        description="Bachelor's degree or higher",
        numerator_codes=("C15002I_006E", "C15002I_011E"),
        denominator_codes=("C15002I_001E",),
    ),
]
