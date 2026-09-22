"""Step 1 of cleaning and transforming: PL renames, race composites, the four targets, and the weight.

Hispanic-of-race counts are derived by subtracting the non-Hispanic portion of
each race from the all-population total (the PL file publishes no direct
Hispanic-by-race lines for the combinations the study needs).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from build_dataset.ingest.pl.nonhispanic_white_total_feats import (
    PL_NONHISPANIC_WHITE_ALONE_OR_COMBINATION,
)
from build_dataset.ingest.pl.white_total_feats import PL_WHITE_ALONE_OR_COMBINATION

RENAME_DICT: dict[str, str] = {
    "P1_001N": "TOTALPOP",
    "P1_003N": "WHITEALONE",
    "P1_008N": "SORALONE",
    "P1_015N": "WHITESOR",
    "P2_002N": "HISPANIC",
    "P2_005N": "NONHISPANICWHITEALONE",
    "P2_010N": "NONHISPANICSORALONE",
    "P2_017N": "NONHISPANICWHITESOR",
}

# --- The columns this step creates (the manifest imports these) --------------
# Named counts: RENAME_DICT's values plus the two summed composites.
PL_COUNT_COLUMNS: tuple[str, ...] = (
    *RENAME_DICT.values(),
    PL_WHITE_ALONE_OR_COMBINATION[0].var_name,
    PL_NONHISPANIC_WHITE_ALONE_OR_COMBINATION[0].var_name,
)

# Hispanic-of-race counts and their complements (`add_hispanic_race_counts`).
HISPANIC_RACE_COUNT_COLUMNS: tuple[str, ...] = (
    "HSOR",
    "H_N_SOR",
    "HWHITESOR",
    "H_N_WHITESOR",
    "HWHITE",
    "H_N_WHITE",
    "HWHITEACOMBO",
    "H_N_WHITEACOMBO",
)

# What the two arms predict, most-reported race choice first: both share
# families (denominator in the name), then the dominant-race classification
# targets.
TARGETS: tuple[str, ...] = (
    "Hisp_Pct_of_Total_Pop",
    "Hisp_SOR_Alone_Pct_of_Total_Pop",
    "Hisp_White_SOR_Pct_of_Total_Pop",
    "Hisp_White_Alone_Pct_of_Total_Pop",
    "Hisp_White_Pct_of_Total_Pop",
    "Hisp_SOR_Alone_Pct_of_Hisp_Pop",
    "Hisp_White_SOR_Pct_of_Hisp_Pop",
    "Hisp_White_Alone_Pct_of_Hisp_Pop",
    "Hisp_White_Pct_of_Hisp_Pop",
    "largest",
    "Most_SOR",
    "Most_White_SOR",
    "Most_White",
)


def add_pl_features_and_rename(df: pd.DataFrame) -> pd.DataFrame:
    """Composites and renames: raw PL codes -> named counts. Calculates the two white-alone-or-in-combination totals."""
    df = df.copy()
    # Each aggregate list holds ONE feature whose numerator_codes are the
    # 32 lines to sum; the dataframe is indexed by those codes, not the
    # feature objects.
    white_combo = PL_WHITE_ALONE_OR_COMBINATION[0]
    nh_white_combo = PL_NONHISPANIC_WHITE_ALONE_OR_COMBINATION[0]
    df[white_combo.var_name] = df[list(white_combo.numerator_codes)].sum(axis=1)
    df[nh_white_combo.var_name] = df[list(nh_white_combo.numerator_codes)].sum(axis=1)
    return df.rename(columns=RENAME_DICT)


def add_hisp_race_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Hispanic-of-race shares of total population and of Hispanic population."""
    df = df.copy()

    total_pop = df["TOTALPOP"].replace(0, np.nan)
    hisp_pop = df["HISPANIC"].replace(0, np.nan)

    df["Hisp_Pct_of_Total_Pop"] = df["HISPANIC"] / total_pop

    df["Hisp_SOR_Alone_Pct_of_Total_Pop"] = df["HSOR"] / total_pop
    df["Hisp_White_Alone_Pct_of_Total_Pop"] = df["HWHITE"] / total_pop
    df["Hisp_White_SOR_Pct_of_Total_Pop"] = df["HWHITESOR"] / total_pop
    df["Hisp_White_Pct_of_Total_Pop"] = df["HWHITEACOMBO"] / total_pop

    df["Hisp_SOR_Alone_Pct_of_Hisp_Pop"] = df["HSOR"] / hisp_pop
    df["Hisp_White_Alone_Pct_of_Hisp_Pop"] = df["HWHITE"] / hisp_pop
    df["Hisp_White_SOR_Pct_of_Hisp_Pop"] = df["HWHITESOR"] / hisp_pop
    df["Hisp_White_Pct_of_Hisp_Pop"] = df["HWHITEACOMBO"] / hisp_pop
    return df


def add_hisp_dominant_race_choice(df: pd.DataFrame) -> pd.DataFrame:
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
    """For each race choice X: Hispanic-of-X (H*) and its complement (H_N_*).

    Example:
        `SORALONE` = total SOR population,
        `NONHISPANICSORALONE` = non-Hispanic SOR population,
        `HSOR` = SORALONE - NONHISPANICSORALONE = Hispanic SOR population,
    """
    df["HSOR"] = df["SORALONE"] - df["NONHISPANICSORALONE"]
    df["H_N_SOR"] = df["HISPANIC"] - df["HSOR"]
    df["HWHITESOR"] = df["WHITESOR"] - df["NONHISPANICWHITESOR"]
    df["H_N_WHITESOR"] = df["HISPANIC"] - df["HWHITESOR"]
    df["HWHITE"] = df["WHITEALONE"] - df["NONHISPANICWHITEALONE"]
    df["H_N_WHITE"] = df["HISPANIC"] - df["HWHITE"]
    df["HWHITEACOMBO"] = df["WHITEALONEORCOMBO"] - df["NONHISPANICWHITEALONEORCOMBO"]
    df["H_N_WHITEACOMBO"] = df["HISPANIC"] - df["HWHITEACOMBO"]
    return df


def clean_and_transform_pl_data(df: pd.DataFrame) -> pd.DataFrame:
    """The full PL step: composites/renames, counts, shares, dominant race."""
    df = add_pl_features_and_rename(df)
    df = add_hispanic_race_counts(df)
    df = add_hisp_race_percentages(df)
    df = add_hisp_dominant_race_choice(df)
    # The declarations above and the code here cannot drift silently: every
    # declared column must actually have been created.
    missing = {*PL_COUNT_COLUMNS, *HISPANIC_RACE_COUNT_COLUMNS, *TARGETS} - set(
        df.columns
    )
    if missing:
        raise KeyError(f"declared PL columns not created: {sorted(missing)}")
    return df
