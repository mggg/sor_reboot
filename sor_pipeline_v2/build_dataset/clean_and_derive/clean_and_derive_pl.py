"""Step 1 of cleaning and transforming: PL counts, race composites, the targets, and the weight.

Every arithmetic column of this step is a declared ModelVariable computed by
its computer; the one hand-written block is the dominant-race classification
(`add_hisp_dominant_race_choice`), whose argmax logic fits no computer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from build_dataset.ingest.pl.feats.hisp_pop_feats import (
    HISPANIC,
    NONHISPANICSORALONE,
    NONHISPANICWHITEALONE,
    NONHISPANICWHITESOR,
    PL_HISP_FEATURES,
)
from build_dataset.ingest.pl.feats.hisp_race_targets import (
    HISP_RACE_COUNTS,
    HISP_RACE_SHARES,
    HSOR,
    HWHITE,
    HWHITESOR,
)
from build_dataset.ingest.pl.feats.nonhispanic_white_total_feats import (
    NONHISPANICWHITEALONEORCOMBO,
    PL_NONHISPANIC_WHITE_ALONE_OR_COMBINATION,
)
from build_dataset.ingest.pl.feats.total_pop_feats import (
    PL_FEATURES,
    SORALONE,
    TOTALPOP,
    WHITEALONE,
    WHITESOR,
)
from build_dataset.ingest.pl.feats.white_total_feats import (
    PL_WHITE_ALONE_OR_COMBINATION,
    WHITEALONEORCOMBO,
)

PL_COUNT_COLUMNS: tuple[str, ...] = (
    TOTALPOP,
    WHITEALONE,
    SORALONE,
    WHITESOR,
    HISPANIC,
    NONHISPANICWHITEALONE,
    NONHISPANICSORALONE,
    NONHISPANICWHITESOR,
    WHITEALONEORCOMBO,
    NONHISPANICWHITEALONEORCOMBO,
)

HISPANIC_RACE_COUNT_COLUMNS: tuple[str, ...] = tuple(
    variable.var_name for variable in HISP_RACE_COUNTS
)

DOMINANT_RACE_INDICATOR = "largest"
MOST_SOR = "Most_SOR"
MOST_WHITE_SOR = "Most_White_SOR"
MOST_WHITE = "Most_White"
CLASSIFICATION_TARGETS: tuple[str, ...] = (
    DOMINANT_RACE_INDICATOR,
    MOST_SOR,
    MOST_WHITE_SOR,
    MOST_WHITE,
)


TARGETS: tuple[str, ...] = (
    *(variable.var_name for variable in HISP_RACE_SHARES),
    *CLASSIFICATION_TARGETS,
)


def add_pl_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Compute every declared PL fetch-list variable from its variable_computer.

    The raw code columns stay in the frame; the manifest's processed-column
    selection is what drops them at the end of the build.

    Parameters
    ----------
    df : pandas.DataFrame
        The merged frame after numeric coercion, containing every raw PL
        code column (P1_*, P2_*).

    Returns
    -------
    pandas.DataFrame
        A copy with one new column per declared PL variable.

    Raises
    ------
    KeyError
        If a raw PL code column a computer reads is absent -- the step ran
        before the PL fetch was merged.
    """
    df = df.copy()
    for variable in (
        *PL_FEATURES,
        *PL_HISP_FEATURES,
        *PL_WHITE_ALONE_OR_COMBINATION,
        *PL_NONHISPANIC_WHITE_ALONE_OR_COMBINATION,
    ):
        df[variable.var_name] = variable.variable_computer(df)
    return df


def add_hisp_race_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the declared Hispanic-of-race counts, then the share targets.

    List order is load-bearing: complements read the counts declared before
    them, and every share reads a count, so HISP_RACE_COUNTS runs first.

    Parameters
    ----------
    df : pandas.DataFrame
        The frame after `add_pl_counts`, containing every PL count column
        the target computers read (TOTALPOP, HISPANIC, the race counts).

    Returns
    -------
    pandas.DataFrame
        A copy with the count and share target columns added.

    Raises
    ------
    KeyError
        If a count column a computer reads is absent -- the step ran
        before `add_pl_counts`.
    """
    df = df.copy()
    for variable in (*HISP_RACE_COUNTS, *HISP_RACE_SHARES):
        df[variable.var_name] = variable.variable_computer(df)
    return df


def add_hisp_dominant_race_choice(df: pd.DataFrame) -> pd.DataFrame:
    """Add `largest` (1=SOR, 2=White+SOR, 3=White alone) and the Most_* one-hots.

    Ranks the raw counts: same ordering as ranking either share family (the
    denominator is common), with no NaN comparisons where a denominator is 0.

    Parameters
    ----------
    df : pandas.DataFrame
        The frame after `add_hisp_race_targets`, containing HSOR, HWHITE,
        and HWHITESOR. Modified in place and returned.

    Returns
    -------
    pandas.DataFrame
        The frame with the four classification columns
        (CLASSIFICATION_TARGETS) added.

    Raises
    ------
    KeyError
        If a Hispanic-of-race count column is absent -- the step ran
        before `add_hisp_race_targets`.
    """
    conditions = [
        (df[HSOR] >= df[HWHITE]) & (df[HSOR] >= df[HWHITESOR]),
        (df[HWHITE] >= df[HSOR]) & (df[HWHITE] >= df[HWHITESOR]),
    ]
    df[DOMINANT_RACE_INDICATOR] = np.select(conditions, [1, 3], default=2)
    df[MOST_SOR] = (df[DOMINANT_RACE_INDICATOR] == 1).astype(int)
    df[MOST_WHITE_SOR] = (df[DOMINANT_RACE_INDICATOR] == 2).astype(int)
    df[MOST_WHITE] = (df[DOMINANT_RACE_INDICATOR] == 3).astype(int)
    return df


def clean_and_transform_pl_data(df: pd.DataFrame) -> pd.DataFrame:
    """The full PL step: counts, Hispanic-of-race counts, shares, dominant race.

    Parameters
    ----------
    df : pandas.DataFrame
        The merged frame after numeric coercion, containing every raw PL
        code column.

    Returns
    -------
    pandas.DataFrame
        The frame with every PL-declared column added: the count
        composites, the Hispanic-of-race counts, both share families, and
        the classification targets.

    Raises
    ------
    KeyError
        If a raw PL code column is absent (fetch not merged), or -- from
        the exit check -- if a column this step declares was not actually
        created, meaning the declarations and the code have drifted.
    """
    df = add_pl_counts(df)
    df = add_hisp_race_targets(df)
    df = add_hisp_dominant_race_choice(df)

    missing = {*PL_COUNT_COLUMNS, *HISPANIC_RACE_COUNT_COLUMNS, *TARGETS} - set(
        df.columns
    )
    if missing:
        raise KeyError(f"declared PL columns not created: {sorted(missing)}")

    return df
