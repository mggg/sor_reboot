"""What each column MEANS: its display name, its formula, its universe.

A histogram of GUATEMALANORIGIN is unreadable without knowing whether
its denominator is everybody or only Hispanic residents. That answer is
already in the declarations -- every column is a ModelVariable carrying
a `variable_computer` that names its numerator and denominator -- so it
is rendered from there rather than written out again here, and cannot
drift from what the build actually computed.

The census code enums carry readable member names
(HISPANIC_POPULATION_B03001), which is what makes a formula line worth
printing.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import assert_never

from build_dataset.ingest.acs.feats import (
    CITIZENSHIP_FEATURES,
    EDUCATION_FEATURES,
    EMPLOYMENT_FEATURES,
    HOUSEHOLD_FEATURES,
    INCOME_FEATURES,
    LANGUAGE_FEATURES,
    MOBILITY_FEATURES,
    NATIONAL_ORIGIN_FEATURES,
    RACIAL_ETHNIC_FEATURES,
)
from build_dataset.ingest.declarations.feature_utils import (
    Difference,
    FractionalShare,
    LogGrowth,
    ModelVariable,
    Passthrough,
    SignedLean,
    SumFeature,
    VariableComputer,
)
from build_dataset.ingest.dhc.dhc_feats import DHC_FEATURES
from build_dataset.ingest.election.election_feats import ELECTION_FEATURES
from build_dataset.ingest.geometry.geometry_feats import GEOMETRY_FEATURES
from build_dataset.ingest.pl.feats.hisp_pop_feats import PL_HISP_FEATURES
from build_dataset.ingest.pl.feats.hisp_race_targets import (
    HISP_RACE_COUNTS,
    HISP_RACE_SHARES,
)
from build_dataset.ingest.pl.feats.nonhispanic_white_total_feats import (
    PL_NONHISPANIC_WHITE_ALONE_OR_COMBINATION,
)
from build_dataset.ingest.pl.feats.total_pop_feats import PL_FEATURES
from build_dataset.ingest.pl.feats.white_total_feats import (
    PL_WHITE_ALONE_OR_COMBINATION,
)

DECLARATION_LISTS: tuple[list[ModelVariable], ...] = (
    CITIZENSHIP_FEATURES,
    EDUCATION_FEATURES,
    EMPLOYMENT_FEATURES,
    HOUSEHOLD_FEATURES,
    INCOME_FEATURES,
    LANGUAGE_FEATURES,
    MOBILITY_FEATURES,
    NATIONAL_ORIGIN_FEATURES,
    RACIAL_ETHNIC_FEATURES,
    DHC_FEATURES,
    ELECTION_FEATURES,
    GEOMETRY_FEATURES,
    PL_FEATURES,
    PL_HISP_FEATURES,
    HISP_RACE_COUNTS,
    HISP_RACE_SHARES,
    PL_NONHISPANIC_WHITE_ALONE_OR_COMBINATION,
    PL_WHITE_ALONE_OR_COMBINATION,
)

# Census code enums append their table to the member name
# (HISPANIC_POPULATION_B03001); the table is already in the code itself.
TABLE_SUFFIX = re.compile(r"_[A-Z]?\d{5}[A-Z]?$")


@dataclass(frozen=True)
class ColumnMeaning:
    """One column's human-facing description."""

    column: str
    display_name: str
    description: str
    formula: str
    universe: str


def _readable(code: str) -> str:
    """A census code's enum member name as English, or the raw code.

    Parameters
    ----------
    code : str
        A StrEnum member from the code declarations, or a plain string
        for the columns the pipeline names itself (vote columns).

    Returns
    -------
    str
        e.g. HISPANIC_POPULATION_B03001 -> "hispanic population".
    """
    if not isinstance(code, Enum):
        return code
    return TABLE_SUFFIX.sub("", code.name).replace("_", " ").lower()


def _sum_label(codes: Sequence[str], max_named_chars: int = 40) -> str:
    """Summed codes as English, naming terms up to `max_named_chars`.

    Parameters
    ----------
    codes : sequence of str
        Census codes, or column names the pipeline gives itself.
    max_named_chars : int
        How many characters of term names to spell out; the remaining
        terms are counted instead. A single code is always named in full.

    Returns
    -------
    str
        e.g. "white alone + white black or african american + 30 more",
        or "sum of 14 components" when not even one name fits.
    """
    names = [_readable(code) for code in codes]
    if len(names) == 1:
        return names[0]

    named: list[str] = []
    used = 0
    for name in names:
        if named and used + len(name) + 3 > max_named_chars:
            break
        used += len(name) + (3 if named else 0)
        named.append(name)

    if len(named) == len(names):
        return " + ".join(names)

    if not named or used > max_named_chars:
        return f"sum of {len(names)} components"
    return " + ".join(named) + f" + {len(names) - len(named)} more"


def _render(computer: VariableComputer) -> tuple[str, str]:
    """A computer as (formula, universe).

    `universe` answers the question a share raises -- a share OF WHAT --
    and is empty for a column that is a level rather than a share.
    """
    match computer:
        case FractionalShare(numerator_codes=numerator, denominator_codes=denominator):
            top = _sum_label(numerator)
            if not denominator:
                return top, ""
            bottom = _sum_label(denominator)
            top = f"({top})" if len(numerator) > 1 else top
            bottom = f"({bottom})" if len(denominator) > 1 else bottom
            return f"{top} / {bottom}", bottom
        case SumFeature(codes=codes):
            return _sum_label(codes), ""
        case Passthrough(code=code):
            return _readable(code), ""
        case Difference(minuend_code=minuend, subtrahend_code=subtrahend):
            return f"{_readable(minuend)} - {_readable(subtrahend)}", ""
        case LogGrowth(current_code=current, prior_code=prior):
            return f"log1p({_readable(current)}) - log1p({_readable(prior)})", ""
        case SignedLean(positive_codes=positive, negative_codes=negative):
            plus = _sum_label(positive)
            minus = _sum_label(negative)
            return f"({plus} - {minus}) / ({plus} + {minus})", f"{plus} + {minus}"
        case _:
            assert_never(computer)


def column_meanings() -> dict[str, ColumnMeaning]:
    """Every declared column's meaning, keyed by column name."""
    meanings: dict[str, ColumnMeaning] = {}
    for declarations in DECLARATION_LISTS:
        for variable in declarations:
            formula, universe = _render(variable.variable_computer)
            meanings[variable.var_name] = ColumnMeaning(
                column=variable.var_name,
                display_name=variable.display_name,
                description=variable.description,
                formula=formula,
                universe=universe,
            )
    return meanings


def meaning_for(column: str, meanings: dict[str, ColumnMeaning]) -> ColumnMeaning:
    """One column's meaning, falling back to its bare name."""
    return meanings.get(column, ColumnMeaning(column, column, "", "", ""))
