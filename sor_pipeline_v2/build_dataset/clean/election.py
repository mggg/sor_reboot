"""Step 5: VOTELEAN, NUMBEROFVOTERS, TURNOUT from the raw vote columns.

Depends on step 2: TURNOUT's denominator (VOTINGAGEPOP) is an ACS auxiliary
column born in the ACS step. Puerto Rico's 78 municipios have NaN vote columns
(no presidential vote) and correctly come out NaN in all three features.

A handful of counties exceed TURNOUT = 1.0: VOTINGAGEPOP is a survey estimate
of a slightly different quantity (residents, not eligible voters) and the two
sources need not agree exactly. That is a caveat, not an error.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_election_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the three political-preference features."""
    if "VOTINGAGEPOP" not in df.columns:
        raise KeyError(
            "VOTINGAGEPOP absent -- add_election_features must run after the "
            "ACS step (clean.acs.add_acs_features), which creates it from "
            "acs_spec.AUXILIARY."
        )
    df = df.copy()
    total = df["E_20_PRES_DEM"] + df["E_20_PRES_REP"]
    # Guard against divide-by-zero where a unit has no two-party votes.
    df["VOTELEAN"] = np.where(
        total == 0, np.nan, (df["E_20_PRES_REP"] - df["E_20_PRES_DEM"]) / total
    )
    df["NUMBEROFVOTERS"] = total
    df["TURNOUT"] = df["NUMBEROFVOTERS"] / df["VOTINGAGEPOP"].replace(0, np.nan)
    return df
