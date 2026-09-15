"""Step 1: PL renames, race composites, the four targets, and the weight.

Hispanic-of-race counts are derived by subtracting the non-Hispanic portion of
each race from the all-population total (the PL file publishes no direct
Hispanic-by-race lines for the combinations the study needs).

Every share is stored under a name that says its denominator: `... Pct of Pop`
(share of everyone, the descriptive convention) and `... Pct of Hisp` (share of
the county's Hispanic residents, what the regression arm predicts). Both
families live in the processed dataset, so no downstream stage ever recomputes
a share -- recomputing one family at modeling time under the other's column
names would leave one name meaning two numbers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from build_dataset.ingest.pl.pl_vars import (
    NON_HISP_WHITE_TOTAL_COLS,
    RENAME_DICT,
    WHITE_TOTAL_COLS,
)


def add_pl_features(df: pd.DataFrame) -> pd.DataFrame:
    """Composites and renames: raw PL codes -> named counts.

    Composites are summed from the raw codes BEFORE the rename, because the
    rename covers only the eight headline counts; the white-alone-or-in-
    combination totals are sums over 35 and 32 lines respectively.
    """
    df = df.copy()
    df["WHITEALONEORCOMBO"] = df[WHITE_TOTAL_COLS].sum(axis=1)
    df["NONHISPANICWHITEALONEORCOMBO"] = df[NON_HISP_WHITE_TOTAL_COLS].sum(axis=1)
    return df.rename(columns=RENAME_DICT)


def add_race_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """Both share families for each Hispanic race choice, denominator in the name.

    `Pct of Pop` divides by TOTALPOP ("10% of the county is Hispanic-SOR");
    `Pct of Hisp` divides by HISPANIC ("50% of the county's Hispanics chose
    SOR" -- the regression targets). Numerators are the counts
    `add_hispanic_race_counts` stored, so the race arithmetic lives only there.

    Zero denominators yield NaN, not inf: a unit with no Hispanic residents
    has no within-Hispanic share. (Counties never hit this; tracts do.)
    """
    pop = df["TOTALPOP"].replace(0, np.nan)
    hisp = df["HISPANIC"].replace(0, np.nan)

    df["Hisp Pct of Pop"] = df["HISPANIC"] / pop

    df["Hisp SOR Alone Pct of Pop"] = df["HSOR"] / pop
    df["Hisp White Alone Pct of Pop"] = df["HWHITE"] / pop
    df["Hisp White SOR Pct of Pop"] = df["HWHITESOR"] / pop
    df["Hisp White Pct of Pop"] = df["HWHITEACOMBO"] / pop

    df["Hisp SOR Alone Pct of Hisp"] = df["HSOR"] / hisp
    df["Hisp White Alone Pct of Hisp"] = df["HWHITE"] / hisp
    df["Hisp White SOR Pct of Hisp"] = df["HWHITESOR"] / hisp
    df["Hisp White Pct of Hisp"] = df["HWHITEACOMBO"] / hisp
    return df


def add_dominant_race_choice(df: pd.DataFrame) -> pd.DataFrame:
    """Add `largest` (1=SOR, 2=White+SOR, 3=White alone) and the Most_* one-hots.

    Ranks the raw counts: same ordering as ranking either share family (the
    denominator is common), with no NaN comparisons where a denominator is 0.
    """
    conditions = [
        (df["HSOR"] >= df["HWHITE"]) & (df["HSOR"] >= df["HWHITESOR"]),
        (df["HWHITE"] >= df["HSOR"]) & (df["HWHITE"] >= df["HWHITESOR"]),
    ]
    df["largest"] = np.select(conditions, [1, 3], default=2)
    df["Most_SOR"] = (df["largest"] == 1).astype(int)
    df["Most_White_SOR"] = (df["largest"] == 2).astype(int)
    df["Most_White"] = (df["largest"] == 3).astype(int)
    return df


def add_hispanic_race_counts(df: pd.DataFrame) -> pd.DataFrame:
    """For each race choice X: Hispanic-of-X (H*) and its complement (H_N_*)."""
    df["HSOR"] = df["SORALONE"] - df["NONHISPANICSORALONE"]
    df["H_N_SOR"] = df["HISPANIC"] - df["HSOR"]
    df["HWHITESOR"] = df["WHITESOR"] - df["NONHISPANICWHITESOR"]
    df["H_N_WHITESOR"] = df["HISPANIC"] - df["HWHITESOR"]
    df["HWHITE"] = df["WHITEALONE"] - df["NONHISPANICWHITEALONE"]
    df["H_N_WHITE"] = df["HISPANIC"] - df["HWHITE"]
    df["HWHITEACOMBO"] = df["WHITEALONEORCOMBO"] - df["NONHISPANICWHITEALONEORCOMBO"]
    df["H_N_WHITEACOMBO"] = df["HISPANIC"] - df["HWHITEACOMBO"]
    return df


def add_targets(df: pd.DataFrame) -> pd.DataFrame:
    """The full PL step: composites/renames, counts, shares, dominant race.

    Counts come first -- the share and dominant-race steps consume them.
    """
    df = add_pl_features(df)
    df = add_hispanic_race_counts(df)
    df = add_race_percentages(df)
    df = add_dominant_race_choice(df)
    return df
