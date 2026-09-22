"""Step 2: the ACS features -- 87 shares, the derived ratio, the growth pair.

Order of operations matters and is fixed here:

    sentinels -> NaN
      -> sum the component lines (a missing component poisons the sum)
      -> divide by the denominator (a zero universe is an undefined share)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from build_dataset.ingest.acs.feats import PRIOR_CODES, PRIOR_SUFFIX
from build_dataset.ingest.feature_utils import ModelFeature

# Values the API substitutes for a real number. Each means the estimate or
# margin could not be produced; all of them must become NaN before arithmetic,
# because they are large and negative -- they do not look like missing data,
# they look like plausible arithmetic.
SENTINELS: dict[int, str] = {
    -666666666: "estimate cannot be computed (too few sample cases)",
    -999999999: "estimate not available",
    -555555555: "margin cannot be computed, or falls in the lowest/highest interval",
    -222222222: "estimate controlled -- margin not appropriate",
    -333333333: "margin not appropriate for this median",
    -888888888: "not applicable",
}


def nullify_sentinels(df: pd.DataFrame) -> pd.DataFrame:
    """Replace every ACS sentinel value with NaN, across all numeric columns."""
    df = df.copy()
    numeric = df.select_dtypes("number").columns
    block = df[numeric]
    df[numeric] = block.mask(block.isin(list(SENTINELS)))
    return df


def combine_estimates(df: pd.DataFrame, codes: tuple[str, ...]) -> pd.Series:
    """Sum estimate columns; one missing component makes the sum missing."""
    if len(codes) == 1:
        return df[codes[0]]
    return df[list(codes)].sum(axis=1, skipna=False)


def add_acs_features(
    df: pd.DataFrame, model_features: list[ModelFeature]
) -> pd.DataFrame:
    """Derive every ACS feature, diagnostic, and auxiliary column in place."""
    df = df.copy()
    features_to_check = {
        code
        for feature in model_features
        for code in feature.numerator_codes + feature.denominator_codes
    }
    missing = [c for c in features_to_check if c not in df.columns]
    if missing:
        raise KeyError(
            f"{len(missing)} required ACS estimate column(s) absent, first few: "
            f"{missing[:5]}. The fetch and the feats declarations have drifted "
            "apart -- re-run ingest with the current acs_api.all_codes()."
        )

    df = nullify_sentinels(df)

    for feature in model_features:
        if feature.custom:
            continue  # built by its dedicated function, not the generic loop
        num = combine_estimates(df, feature.numerator_codes)
        if feature.denominator_codes:
            # A zero universe is undefined.
            den = combine_estimates(df, feature.denominator_codes).replace(0, np.nan)
            df[feature.var_name] = num / den
        else:
            # Counts and medians pass through untouched; nothing to divide by.
            df[feature.var_name] = num
    return df


def add_custom_growth_features(df: pd.DataFrame) -> pd.DataFrame:
    """The two custom ACS features: growth as a log ratio across vintages.

    These do not follow the generic numerator/denominator pattern, so they are
    computed here in the clean stage."""
    # The declared prior-vintage fetch must cover exactly these inputs.
    assert set(PRIOR_CODES) == {"B03001_003E", "B05002_013E"}

    # NaN where a unit did not exist in 2011-2015
    def growth(code: str) -> pd.Series:
        return np.log1p(df[code]) - np.log1p(df[code + PRIOR_SUFFIX])

    df["HISPGROWTH"] = growth("B03001_003E")
    df["FBGROWTH"] = growth("B05002_013E")
    return df


def main_acs_clean_and_transform(
    df: pd.DataFrame, model_features: list[ModelFeature]
) -> pd.DataFrame:
    """The full ACS step: sentinels, sums, shares, growth."""
    df = add_acs_features(df, model_features)
    df = add_custom_growth_features(df)
    return df
