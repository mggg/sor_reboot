"""Step 5: the election features, each computed by its declared computer.

Depends on step 2: TURNOUT's denominator (VOTINGAGEPOP) is an ACS feature
born in the ACS step. Puerto Rico's 78 municipios have NaN vote columns
(no presidential vote) and correctly come out NaN in all three features.

Which features are asked for is the caller's choice, because the two
levels have different inputs: counties carry both 2016 and 2020 votes and
so support all five, while tracts carry 2020 only (VEST 2016 has not been
prorated) and so ask for the three that need no prior year.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from build_dataset.ingest.declarations.feature_utils import ModelVariable
from build_dataset.ingest.election.election_feats import ELECTION_FEATURES


def add_election_features(
    df: pd.DataFrame,
    features: Sequence[ModelVariable] = ELECTION_FEATURES,
) -> pd.DataFrame:
    """Derive the requested election features from their computers.

    Parameters
    ----------
    df : pandas.DataFrame
        The merged frame after the ACS step, containing the raw vote
        columns the requested features read and VOTINGAGEPOP.
    features : sequence of ModelVariable
        Which election variables to compute; every declared one by
        default. A level that lacks an input year passes the subset its
        votes support, and the inputs of the features it leaves out are
        then not required.

    Returns
    -------
    pandas.DataFrame
        A copy with one new column per requested election variable.

    Raises
    ------
    KeyError
        If an input column is absent -- the step ran before the election
        merge or before the ACS step that creates VOTINGAGEPOP.
    """
    required = {
        column
        for variable in features
        for column in variable.variable_computer.input_columns()
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise KeyError(
            f"election inputs absent: {missing} -- add_election_features must "
            "run after the election merge and the ACS step (which creates "
            "VOTINGAGEPOP)."
        )
    df = df.copy()
    for variable in features:
        df[variable.var_name] = variable.variable_computer(df)
    return df
