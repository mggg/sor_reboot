"""The ACS feature declarations, grouped by ACS section."""

from build_dataset.ingest.feature_utils import ModelFeature

from .citizenship_feats import CITIZENSHIP_FEATURES
from .education_feats import EDUCATION_FEATURES
from .employment_feats import EMPLOYMENT_FEATURES
from .household_feats import HOUSEHOLD_FEATURES
from .income_feats import INCOME_FEATURES
from .language_feats import LANGUAGE_FEATURES
from .mobility_feats import MOBILITY_FEATURES
from .mobility_feats import (
    PRIOR_CODES as PRIOR_CODES,
)
from .mobility_feats import (
    PRIOR_SUFFIX as PRIOR_SUFFIX,
)
from .national_origin_feats import NATIONAL_ORIGIN_FEATURES
from .racial_ethnic_feats import RACIAL_ETHNIC_FEATURES

ACS_FEATURES: list[ModelFeature] = [
    *CITIZENSHIP_FEATURES,
    *EDUCATION_FEATURES,
    *EMPLOYMENT_FEATURES,
    *HOUSEHOLD_FEATURES,
    *INCOME_FEATURES,
    *LANGUAGE_FEATURES,
    *MOBILITY_FEATURES,
    *NATIONAL_ORIGIN_FEATURES,
    *RACIAL_ETHNIC_FEATURES,
]
