"""DHC features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.feature_utils import ModelFeature

DHC_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="DHC_P2",
        table_code=None,
        var_name="URBANSHARE",
        description="Share of the county's total population living in an urban "
        "area (2020 Census urban/rural classification)",
        numerator_codes=("P2_002N",),
        denominator_codes=("P2_001N",),
    ),
]
