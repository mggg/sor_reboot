"""The margin-of-error algebra. Pure formulas, no I/O, no dataset knowledge.

The ACS is a sample survey, so every estimate column has a `..._M` twin
carrying its 90% margin of error. These formulas carry that margin through
the same arithmetic the clean stage applies to the estimates:

  - summed lines: margins combine in quadrature, not by addition (adding
    overstates the combined margin);
  - shares: the Census derived-proportion formula;
  - "how noisy, relatively": the coefficient of variation.

Reference: "Understanding and Using ACS Data: What All Data Users Need to
Know", U.S. Census Bureau, Appendix 3.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# The 90% margin published by the ACS is 1.645 standard errors.
Z90 = 1.645


def combine_moe(df: pd.DataFrame, codes: tuple[str, ...]) -> pd.Series:
    """Margin of a sum of estimates: `sqrt(MOE_a**2 + MOE_b**2 + ...)`.

    Takes ESTIMATE codes and looks up their `M` twins itself, so callers pass
    the same code list they pass to `combine_estimates` and cannot pair an
    estimate with the wrong margin.
    """
    moe_cols = [code[:-1] + "M" for code in codes]
    if len(moe_cols) == 1:
        return df[moe_cols[0]].abs()
    squared = df[moe_cols].pow(2).sum(axis=1, skipna=False)
    return np.sqrt(squared)


def proportion_moe(
    num_est: pd.Series,
    num_moe: pd.Series,
    den_est: pd.Series,
    den_moe: pd.Series,
) -> pd.Series:
    """Margin of error for the share `num_est / den_est`.

    The derived-PROPORTION formula subtracts the denominator's contribution,
    because the numerator is a subset of the denominator:

        MOE(p) = (1 / den) * sqrt(MOE_num**2 - p**2 * MOE_den**2)

    Where the radicand goes negative (shares near 1, margins nearly equal),
    the Census instructs falling back to the derived-RATIO formula, which
    adds instead of subtracts.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        p = num_est / den_est
        subtractive = num_moe**2 - (p**2) * (den_moe**2)
        additive = num_moe**2 + (p**2) * (den_moe**2)
        radicand = np.where(subtractive >= 0, subtractive, additive)
        moe = np.sqrt(radicand) / den_est
    return pd.Series(moe, index=num_est.index).replace([np.inf, -np.inf], np.nan)


def coefficient_of_variation(estimate: pd.Series, moe: pd.Series) -> pd.Series:
    """Standard error as a fraction of the estimate: `(MOE / 1.645) / estimate`.

    Conventional readability: CV <= 0.15 reliable, 0.15-0.30 use with caution,
    > 0.30 unreliable.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        cv = (moe / Z90) / estimate.abs()
    return pd.Series(cv, index=estimate.index).replace([np.inf, -np.inf], np.nan)


def unreliable_mask(estimate: pd.Series, moe: pd.Series) -> pd.Series:
    """True where the survey cannot distinguish the estimate from zero.

    The rule is `estimate - moe < 0`: the lower bound of the 90% interval
    falls below zero. This FLAGS cells; nothing here (or anywhere in v2)
    discards them -- an imprecise point estimate weakens one feature, while
    nulling it would cost a complete-case model the whole unit.

    Zero counts are exempt: the ACS publishes a fixed minimum margin on any
    zero estimate, so the rule would otherwise flag every genuine zero.
    "This county has no Venezuelan residents" is correct data whose share is
    exactly 0.0, not a measurement the survey failed to make.
    """
    return ((estimate - moe) < 0) & (estimate != 0)
