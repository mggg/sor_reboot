"""Per-feature measurement reliability, computed from the raw artifact.

Answers the two questions the descriptive stats table raises but cannot
answer:

  1. WHY is each feature's data missing? Every NaN in a feature traces to a
     cause visible in the raw columns: the Census declined to estimate
     (sentinel), the feature's universe is empty in that county (zero
     denominator), or a component line is absent.
  2. Where present, how PRECISE is it? A cell is flagged imprecise when the
     survey cannot distinguish its numerator from zero (see
     `moe.unreliable_mask`). Flags describe the data; they never change it.

Works on `raw.parquet` -- the only artifact carrying the `..._M` margin
columns -- re-running the same coercion/sentinel/summation steps clean uses,
imported from clean so the two can never disagree.
"""

from __future__ import annotations

import pandas as pd

from build_dataset.clean.acs import SENTINELS, combine_estimates, nullify_sentinels
from build_dataset.clean.coerce import coerce_numeric
from build_dataset.ingest.acs import acs_spec
from feature_report.moe import combine_moe, unreliable_mask


def feature_reliability(raw: pd.DataFrame) -> pd.DataFrame:
    """One row per ACS feature: missingness causes and imprecision counts.

    Covers the spec's ACS features only -- the other sources (PL, DHC,
    geometry, election) are complete counts or administrative records with no
    survey margin, so reliability in this sense does not apply to them.
    """
    df = coerce_numeric(raw)
    est_codes = acs_spec.estimate_codes()
    sentinel_hit = df[est_codes].isin(list(SENTINELS))
    clean = nullify_sentinels(df)

    rows = []
    for feature in acs_spec.iter_features():
        codes = list(feature.numerator_codes + feature.denominator_codes)
        num = combine_estimates(clean, feature.numerator_codes)
        num_moe = combine_moe(clean, feature.numerator_codes)

        if feature.is_share:
            den = combine_estimates(clean, feature.denominator_codes)
            zero_universe = den == 0
            value = num / den.replace(0, pd.NA)
        else:
            zero_universe = pd.Series(False, index=df.index)
            value = num

        missing = value.isna()
        from_sentinel = missing & sentinel_hit[codes].any(axis=1)
        from_zero_universe = missing & zero_universe & ~from_sentinel
        imprecise = unreliable_mask(num, num_moe).fillna(False)

        rows.append(
            {
                "feature": feature.name,
                "n_missing": int(missing.sum()),
                # why missing: the Census printed a cannot-compute code ...
                "n_missing_census_decline": int(from_sentinel.sum()),
                # ... or the feature's universe is empty there (0/0, a question
                # about nobody) ...
                "n_missing_due_to_empty_denominator": int(from_zero_universe.sum()),
                # ... or no value was published at all -- whole tables for
                # Puerto Rico (B05005/B07004I), scattered cells elsewhere.
                "n_missing_unpublished": int(
                    (missing & ~from_sentinel & ~from_zero_universe).sum()
                ),
                # a value EXISTS but its 90% interval reaches zero: too fuzzy
                # to trust on its own. Flagged, never altered.
                "n_cant_rule_out_zero": int(imprecise.sum()),
                "pct_cant_rule_out_zero": round(100 * imprecise.mean(), 2),
            }
        )
    return pd.DataFrame(rows)
