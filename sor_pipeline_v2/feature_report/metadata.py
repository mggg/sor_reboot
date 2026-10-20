"""What each column MEANS: its display name, its formula, its universe.

A histogram of GUATEMALANORIGIN is unreadable without knowing whether
its denominator is everybody or only Hispanic residents. That answer is
already in the declarations -- every column is a ModelVariable carrying
a `variable_computer` that names its numerator and denominator -- so it
is rendered from there rather than written out again here, and cannot
drift from what the build actually computed.

The census code enums carry readable member names
(HISPANIC_POPULATION_B03001), which is what makes a formula line worth
printing. Only the dominant-choice columns are described by hand: they
are built inside a derive step rather than declared, so there is no
computer to read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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
from build_dataset.ingest.declarations.feature_utils import ModelVariable
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

# Every declaration list in the project. A column absent from all of
# them falls back to HAND_WRITTEN, then to its own name.
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

# Built by `add_hisp_dominant_race_choice`, not declared, so there is no
# computer to render and no description to inherit.
HAND_WRITTEN: dict[str, tuple[str, str]] = {
    "largest": (
        "Largest Hispanic race choice",
        (
            "Which choice the most Hispanic residents selected: "
            "1 = SOR alone, 2 = White and SOR, 3 = White alone"
        ),
    ),
    "Most_SOR": (
        "SOR alone is largest",
        "1 where SOR alone is the most-selected Hispanic race choice, else 0",
    ),
    "Most_White_SOR": (
        "White and SOR is largest",
        "1 where White and SOR is the most-selected Hispanic race choice, else 0",
    ),
    "Most_White": (
        "White alone is largest",
        "1 where White alone is the most-selected Hispanic race choice, else 0",
    ),
}

# Census code enums append their table to the member name
# (HISPANIC_POPULATION_B03001); the table is already in the code itself.
TABLE_SUFFIX = re.compile(r"_[A-Z]?\d{5}[A-Z]?$")

# A formula is a label, not a specification. Some sum dozens of census
# categories -- NONHISPANICWHITEALONEORCOMBO adds 32, which spells out
# to 3,010 characters -- and nobody reads that off a chart. Each side of
# a ratio gets this many characters to name terms in; whatever does not
# fit is counted instead. Budgeting by LENGTH rather than by term count
# is what lets the result always fit on one line, so nothing downstream
# has to truncate it. The declaration remains the authority on what was
# actually summed.
SIDE_BUDGET = 40


@dataclass(frozen=True)
class ColumnMeaning:
    """One column's human-facing description."""

    column: str
    display_name: str
    description: str
    formula: str
    universe: str


def _readable(code: object) -> str:
    """A census code's enum member name as English, or the raw code.

    Parameters
    ----------
    code : object
        A StrEnum member from the code declarations, or a plain string
        for the columns the pipeline names itself (vote columns).

    Returns
    -------
    str
        e.g. HISPANIC_POPULATION_B03001 -> "hispanic population".
    """
    name = getattr(code, "name", None)
    if not name:
        return str(code)
    return TABLE_SUFFIX.sub("", name).replace("_", " ").lower()


def _join(codes: object) -> str:
    """Summed codes as English, naming as many as the budget allows.

    Parameters
    ----------
    codes : object
        A sequence of census codes.

    Returns
    -------
    str
        e.g. "white alone + white black or african american + 30 more",
        or "sum of 14 components" when not even one name fits.
    """
    names = [_readable(code) for code in codes]  # type: ignore[union-attr]
    if len(names) == 1:
        return names[0]

    named: list[str] = []
    used = 0
    for name in names:
        if named and used + len(name) + 3 > SIDE_BUDGET:
            break
        used += len(name) + (3 if named else 0)
        named.append(name)

    if len(named) == len(names):
        return " + ".join(names)
    # One term so long it ate the budget on its own says less than a
    # plain count does.
    if not named or used > SIDE_BUDGET:
        return f"sum of {len(names)} components"
    return " + ".join(named) + f" + {len(names) - len(named)} more"


def _render(computer: object) -> tuple[str, str]:
    """A computer as (formula, universe).

    `universe` answers the question a share raises -- a share OF WHAT --
    and is empty for a column that is a level rather than a share.
    """
    numerator = getattr(computer, "numerator_codes", None)
    denominator = getattr(computer, "denominator_codes", None)
    if numerator is not None and denominator is not None:
        top = _join(numerator)
        if not denominator:
            return top, ""
        bottom = _join(denominator)
        # Both sides need their own brackets: "(a + b) / c + d" reads as
        # a sum with a fraction in it rather than one ratio.
        top = f"({top})" if len(numerator) > 1 else top
        bottom = f"({bottom})" if len(denominator) > 1 else bottom
        # The denominator IS the universe: it is what "a share of
        # what?" is asking, and the only part of the formula most
        # readers need.
        return f"{top} / {bottom}", bottom
    if (codes := getattr(computer, "codes", None)) is not None:
        return _join(codes), ""
    if (code := getattr(computer, "code", None)) is not None:
        return _readable(code), ""
    # getattr throughout rather than attribute access: the computers are
    # unrelated classes with no shared protocol, so the checker cannot
    # know which fields any one of them has.
    if (minuend := getattr(computer, "minuend_code", None)) is not None:
        subtrahend = _readable(getattr(computer, "subtrahend_code", ""))
        return f"{_readable(minuend)} - {subtrahend}", ""
    if (current := getattr(computer, "current_code", None)) is not None:
        prior = _readable(getattr(computer, "prior_code", ""))
        return f"log1p({_readable(current)}) - log1p({prior})", ""
    if (positive := getattr(computer, "positive_codes", None)) is not None:
        plus = _join(positive)
        minus = _join(getattr(computer, "negative_codes", ()))
        return f"({plus} - {minus}) / ({plus} + {minus})", f"{plus} + {minus}"
    return "", ""


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
    for column, (display_name, description) in HAND_WRITTEN.items():
        meanings[column] = ColumnMeaning(column, display_name, description, "", "")
    return meanings


def meaning_for(column: str, meanings: dict[str, ColumnMeaning]) -> ColumnMeaning:
    """One column's meaning, falling back to its bare name."""
    return meanings.get(column, ColumnMeaning(column, column, "", "", ""))
