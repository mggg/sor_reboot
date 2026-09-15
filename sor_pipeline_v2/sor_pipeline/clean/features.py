"""Derived race shares, ratios, dominant-race indicators, and the model feature matrix.

Migrated from `3hispaniccleanjune` cell 4 and the feature-building in
`nationhispanicraceprediction`. Hispanic-of-race counts are derived by subtracting
the non-Hispanic portion of each race from the all-population total.
"""

from __future__ import annotations
import pandas as pd
import numpy as np


def add_race_percentages(
    df: pd.DataFrame, denominator: str = "TOTALPOP"
) -> pd.DataFrame:
    """Add Hisp SOR / White-alone / White+SOR shares.

    `denominator="TOTALPOP"` -> share of population (descriptive notebook);
    `denominator="HISPANIC"` -> within-Hispanic share (prediction targets).
    """
    df["Hisp PL Percent"] = (
        df["HISPANIC"] / df["TOTALPOP"]
    )  # always TOTALPOP, not denominator
    df["Hisp SOR Alone PL Percent"] = (df["SORALONE"] - df["NONHISPANICSORALONE"]) / df[
        denominator
    ]
    df["Hisp White Alone PL Percent"] = (
        df["WHITEALONE"] - df["NONHISPANICWHITEALONE"]
    ) / df[denominator]
    df["Hisp White SOR PL Percent"] = (df["WHITESOR"] - df["NONHISPANICWHITESOR"]) / df[
        denominator
    ]
    df["Hisp White PL Percent"] = (
        df["WHITEALONEORCOMBO"] - df["NONHISPANICWHITEALONEORCOMBO"]
    ) / df[denominator]
    return df


def add_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Add each race share as a fraction of the Hispanic share (race-within-Hispanic)."""
    ratio_sources = {
        "Hisp SOR Alone PL Percent": "Hisp SOR Alone_to_Hisp_Ratio",
        "Hisp White Alone PL Percent": "Hisp White Alone_to_Hisp_Ratio",
        "Hisp White SOR PL Percent": "Hisp White SOR_to_Hisp_Ratio",
    }
    for col, new_col in ratio_sources.items():
        df[new_col] = df[col] / df["Hisp PL Percent"]
        df[new_col] = df[new_col].replace([np.inf, -np.inf], np.nan)
    return df


def add_dominant_race_choice(df: pd.DataFrame) -> pd.DataFrame:
    """Add `largest` (1=SOR, 2=White+SOR, 3=White alone) and the Most_* one-hot columns."""
    # largest: 1 = SOR alone, 3 = White alone, 2 = White+SOR (the default).
    conditions = [
        (df["Hisp SOR Alone PL Percent"] >= df["Hisp White Alone PL Percent"])
        & (df["Hisp SOR Alone PL Percent"] >= df["Hisp White SOR PL Percent"]),
        (df["Hisp White Alone PL Percent"] >= df["Hisp SOR Alone PL Percent"])
        & (df["Hisp White Alone PL Percent"] >= df["Hisp White SOR PL Percent"]),
    ]
    choices = [1, 3]
    df["largest"] = np.select(conditions, choices, default=2)

    # One-hot indicator columns for each dominant race (targets for the models)
    df["Most_SOR"] = (df["largest"] == 1).astype(int)
    df["Most_White_SOR"] = (df["largest"] == 2).astype(int)
    df["Most_White"] = (df["largest"] == 3).astype(int)

    # Total two-party votes per county (used as a covariate / size weight)
    df["NUMBEROFVOTERS"] = df["E_20_PRES_DEM"] + df["E_20_PRES_REP"]
    return df


def add_hispanic_race_counts(df: pd.DataFrame) -> pd.DataFrame:
    """For each race choice X: Hispanic-of-X (H*) and its complement (H_N_*)."""
    df = df.copy()
    df["HSOR"] = df["SORALONE"] - df["NONHISPANICSORALONE"]
    df["H_N_SOR"] = df["HISPANIC"] - df["HSOR"]
    df["HWHITESOR"] = df["WHITESOR"] - df["NONHISPANICWHITESOR"]
    df["H_N_WHITESOR"] = df["HISPANIC"] - df["HWHITESOR"]
    df["HWHITE"] = df["WHITEALONE"] - df["NONHISPANICWHITEALONE"]
    df["H_N_WHITE"] = df["HISPANIC"] - df["HWHITE"]
    df["HWHITEACOMBO"] = df["WHITEALONEORCOMBO"] - df["NONHISPANICWHITEALONEORCOMBO"]
    df["H_N_WHITEACOMBO"] = df["HISPANIC"] - df["HWHITEACOMBO"]
    return df
