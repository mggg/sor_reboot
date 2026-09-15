"""Step 2: the ACS features -- 87 shares, the derived ratio, the growth pair.

Order of operations matters and is fixed here:

    sentinels -> NaN
      -> sum the component lines (a missing component poisons the sum)
      -> divide by the denominator (a zero universe is an undefined share)

MOE-based precision flagging is deliberately absent: flags describe the data
and never change it, so feature VALUES need none of that machinery. It lives
in feature_report, which reports on precision without touching the dataset.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from build_dataset.ingest.acs import acs_spec

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
    """Replace every ACS sentinel value with NaN, across all numeric columns.

    Safe as a blanket rule: no real census value is a large negative number --
    counts are non-negative and medians are dollars or years. (`.mask(isin)`
    rather than `.replace([...])`, which trips a pandas reference-tracking bug
    on multi-column blocks in some versions.)
    """
    df = df.copy()
    numeric = df.select_dtypes("number").columns
    block = df[numeric]
    df[numeric] = block.mask(block.isin(list(SENTINELS)))
    return df


def combine_estimates(df: pd.DataFrame, codes: tuple[str, ...]) -> pd.Series:
    """Sum estimate columns; one missing component makes the sum missing.

    A partial sum of a male/female pair is not a total, and silently treating
    the missing half as zero would understate the category.
    """
    if len(codes) == 1:
        return df[codes[0]]
    return df[list(codes)].sum(axis=1, skipna=False)


def add_acs_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive every ACS feature, diagnostic, and auxiliary column in place."""
    missing = [c for c in acs_spec.estimate_codes() if c not in df.columns]
    if missing:
        raise KeyError(
            f"{len(missing)} required ACS estimate column(s) absent, first few: "
            f"{missing[:5]}. The fetch and the spec have drifted apart -- "
            "re-run ingest with the current acs_spec.all_codes()."
        )

    df = nullify_sentinels(df)

    for feature in acs_spec.iter_features():
        num = combine_estimates(df, feature.numerator_codes)
        if feature.is_share:
            # A zero universe is undefined.
            den = combine_estimates(df, feature.denominator_codes).replace(0, np.nan)
            df[feature.name] = num / den
        else:
            # Medians pass through untouched; there is nothing to divide by.
            df[feature.name] = num

    # Derived: children per working-age adult.
    working_age = df["HISP18TO34"] + df["HISP35TO64"]
    df["HISPYOUTHDEP"] = df["HISPUNDER18"] / working_age.replace(0, np.nan)

    # Growth: log ratio of current vs prior-vintage counts. NaN where a unit
    # did not exist in 2011-2015 (Chugach and Copper River, AK).
    for name, code, _meaning in acs_spec.GROWTH_FEATURES:
        df[name] = np.log1p(df[code]) - np.log1p(df[code + acs_spec.PRIOR_SUFFIX])

    # Diagnostics and auxiliaries: renamed copies, never modeled.
    for name, code, _meaning in acs_spec.DIAGNOSTIC:
        df[name] = df[code]
    for name, code, _meaning in acs_spec.AUXILIARY:
        df[name] = df[code]

    return df
