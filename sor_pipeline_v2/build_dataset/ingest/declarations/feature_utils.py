from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal, get_args

import numpy as np
import pandas as pd

# The dataset a feature's raw inputs come from: the two decennial files, the
# ACS 5-year, the TIGER/Line shapefile, or the local election-returns CSV.
SourceName = Literal["PL", "ACS", "DHC", "TIGER", "ELECTION"]

# Sequence[str] (not list[str]): lists are invariant, so list[str] would
# reject a list of StrEnum members (e.g. [Denominator.FOREIGN_BORN]).
# Stored as lists because pandas column selection wants a list.


class FractionalShare:
    """Fractional share of the specified numerator columns over the specified denominator columns.

    Parameters
    ----------
    numerator_codes : sequence of str
        Columns summed into the numerator.
    denominator_codes : sequence of str
        Columns summed into the denominator. If empty, the bare numerator
        sum is returned (a count, not a share).
    """

    def __init__(
        self, numerator_codes: Sequence[str], denominator_codes: Sequence[str]
    ):
        self.numerator_codes = list(numerator_codes)
        self.denominator_codes = list(denominator_codes)

    def input_columns(self) -> list[str]:
        """Return the columns this computer reads (numerators, then denominators)."""
        return self.numerator_codes + self.denominator_codes

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """Compute the share for every row of `df`.

        Parameters
        ----------
        df : pandas.DataFrame
            Merged frame containing every `input_columns()` column, numeric.

        Returns
        -------
        pandas.Series
            One share per row, aligned to df's index. NaN where any input
            component is missing (skipna=False) or the denominator sums to 0.

        Raises
        ------
        KeyError
            If any input column is absent from `df`.
        """
        numerator = df[self.numerator_codes].sum(axis=1, skipna=False)
        if self.denominator_codes:
            denominator = (
                df[self.denominator_codes].sum(axis=1, skipna=False).replace(0, np.nan)
            )
            return numerator / denominator
        return numerator


class SumFeature:
    """Sum of the specified columns.

    Parameters
    ----------
    codes : sequence of str
        Columns to sum. A single code makes this an identity on that
        column's values.
    """

    def __init__(self, codes: Sequence[str]):
        self.codes = list(codes)

    def input_columns(self) -> list[str]:
        """Return the columns this computer reads."""
        return self.codes

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """Compute the row-wise sum.

        Parameters
        ----------
        df : pandas.DataFrame
            Merged frame containing every `input_columns()` column, numeric.

        Returns
        -------
        pandas.Series
            One sum per row, aligned to df's index; NaN where any component
            is missing (skipna=False).

        Raises
        ------
        KeyError
            If any input column is absent from `df`.
        """
        return df[self.codes].sum(axis=1, skipna=False)


class LogGrowth:
    """log1p(current) - log1p(prior): growth across vintages, NaN where the
    unit has no prior-vintage value.

    Parameters
    ----------
    current_code : str
        Column holding the current-period value.
    prior_code : str
        Column holding the prior-period value.
    """

    def __init__(self, current_code: str, prior_code: str):
        self.current_code = current_code
        self.prior_code = prior_code

    def input_columns(self) -> list[str]:
        """Return the columns this computer reads (current, then prior)."""
        return [self.current_code, self.prior_code]

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """Compute the log growth for every row of `df`.

        Parameters
        ----------
        df : pandas.DataFrame
            Merged frame containing both input columns, numeric.

        Returns
        -------
        pandas.Series
            log1p(current) - log1p(prior) per row, aligned to df's index;
            NaN where either period is missing.

        Raises
        ------
        KeyError
            If either input column is absent from `df`.
        """
        growth = np.log1p(df[self.current_code]) - np.log1p(df[self.prior_code])
        return pd.Series(growth, index=df.index)


class SignedLean:
    """(pos - neg) / (pos + neg): a balance on a plus/minus-1 scale, NaN where
    the two sides sum to zero.

    Parameters
    ----------
    positive_codes : sequence of str
        Columns summed into the positive side.
    negative_codes : sequence of str
        Columns summed into the negative side.
    """

    def __init__(self, positive_codes: Sequence[str], negative_codes: Sequence[str]):
        self.positive_codes = list(positive_codes)
        self.negative_codes = list(negative_codes)

    def input_columns(self) -> list[str]:
        """Return the columns this computer reads (positive, then negative)."""
        return self.positive_codes + self.negative_codes

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """Compute the lean for every row of `df`.

        Parameters
        ----------
        df : pandas.DataFrame
            Merged frame containing every `input_columns()` column, numeric.

        Returns
        -------
        pandas.Series
            (pos - neg) / (pos + neg) per row in [-1, 1], aligned to df's
            index; NaN where any component is missing or both sides sum to 0.

        Raises
        ------
        KeyError
            If any input column is absent from `df`.
        """
        positive = df[self.positive_codes].sum(axis=1, skipna=False)
        negative = df[self.negative_codes].sum(axis=1, skipna=False)
        total = (positive + negative).replace(0, np.nan)
        return (positive - negative) / total


class Passthrough:
    """The column as-is; declares a feature whose value needs no arithmetic.

    Parameters
    ----------
    code : str
        The column to pass through unchanged.
    """

    def __init__(self, code: str):
        self.code = code

    def input_columns(self) -> list[str]:
        """Return the single column this computer reads."""
        return [self.code]

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """Return the column unchanged.

        Parameters
        ----------
        df : pandas.DataFrame
            Merged frame containing the input column.

        Returns
        -------
        pandas.Series
            The column's values, aligned to df's index.

        Raises
        ------
        KeyError
            If the column is absent from `df`.
        """
        return df[self.code]


class Difference:
    """minuend - subtrahend: one column minus another.

    Built for the Hispanic-of-race counts, which the PL file publishes no
    direct lines for: Hispanic-X = all-population-X minus non-Hispanic-X.

    Parameters
    ----------
    minuend_code : str
        Column the subtraction starts from.
    subtrahend_code : str
        Column subtracted away.
    """

    def __init__(self, minuend_code: str, subtrahend_code: str):
        self.minuend_code = minuend_code
        self.subtrahend_code = subtrahend_code

    def input_columns(self) -> list[str]:
        """Return the columns this computer reads (minuend, then subtrahend)."""
        return [self.minuend_code, self.subtrahend_code]

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """Compute the difference for every row of `df`.

        Parameters
        ----------
        df : pandas.DataFrame
            Merged frame containing both input columns, numeric.

        Returns
        -------
        pandas.Series
            minuend - subtrahend per row, aligned to df's index; NaN where
            either side is missing.

        Raises
        ------
        KeyError
            If either input column is absent from `df`.
        """
        return df[self.minuend_code] - df[self.subtrahend_code]


VariableComputer = (
    FractionalShare | SumFeature | LogGrowth | SignedLean | Passthrough | Difference
)

# What part a variable plays in modeling: an input (predictor), an output
# the models predict (target), or a column kept for denominators, weights,
# or description only (context).
VariableRole = Literal["predictor", "target", "context"]


@dataclass(frozen=True)
class ModelVariable:
    """A declared variable (column) of the dataset.

    The variable_computer carries the whole computation: which columns of the
    merged frame it reads (`input_columns()`) and how they combine into the
    variable's value (calling it on the frame). The derive stage computes
    every variable as `df[var_name] = variable_computer(df)`. The role says
    what part the variable plays in modeling; most declarations are
    predictors, so that is the default.
    """

    source: SourceName
    var_name: str  # Machine-readable name of the variable
    display_name: str  # Human-readable name of the variable
    description: str
    variable_computer: VariableComputer
    role: VariableRole = "predictor"

    def __post_init__(self) -> None:
        """Validate the declaration at construction time.

        Raises
        ------
        ValueError
            If `source` is not one of the SourceName literals, or `role`
            not one of the VariableRole literals.
        TypeError
        If `variable_computer` is not an instance of a VariableComputer
            class.
        """
        # Annotations are not enforced at runtime; a declaration handing
        # something else here should fail at import, not mid-derive.
        if self.source not in get_args(SourceName):
            raise ValueError(
                f"{self.var_name}: unknown source {self.source!r}; "
                f"known: {get_args(SourceName)}"
            )
        if self.role not in get_args(VariableRole):
            raise ValueError(
                f"{self.var_name}: unknown role {self.role!r}; "
                f"known: {get_args(VariableRole)}"
            )
        if not isinstance(self.variable_computer, VariableComputer):
            raise TypeError(
                f"{self.var_name}: variable_computer must be one of the "
                "VariableComputer classes, got "
                f"{type(self.variable_computer).__name__}"
            )


def feature_codes(features: Iterable[ModelVariable]) -> list[str]:
    """Every distinct column the features' computers read, sorted for a
    stable fetch order.

    Deduplicates -- aggregate features share codes with per-code features, and
    denominators repeat across features of one table. For census sources this
    IS the fetch list; sources whose computers read merged-frame columns
    (prefixed, suffixed, or non-census names) adjust in their own api.

    Parameters
    ----------
    features : iterable of ModelVariable
        The declarations whose input columns to collect.

    Returns
    -------
    list of str
        The sorted union of every computer's `input_columns()`.
    """
    codes: set[str] = set()
    for feature in features:
        codes.update(feature.variable_computer.input_columns())
    return sorted(codes)
