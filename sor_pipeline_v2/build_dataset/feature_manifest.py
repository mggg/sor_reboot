"""Which declared columns the models fit on, and how they group.

The feats packages declare every column ingest produces, and the derive stage
declares the columns it creates (counts and targets, next to the code that
makes them). Each declaration carries its own role (predictor / target /
context), so this module owns only the one judgment nobody else can make:
how the predictors partition into thematic groups. It assembles the
processed.parquet schema from those imported pieces.

The import arrow points one way: the manifest imports from the sources and
the derive stage; neither knows the manifest exists.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, get_args

from build_dataset.clean_and_derive.clean_and_derive_pl import (
    HISPANIC_RACE_COUNT_COLUMNS,
    PL_COUNT_COLUMNS,
    TARGETS,
)
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

SlugGroupName = Literal[
    "language",
    "citizenship",
    "national_origin",
    "mobility",
    "education",
    "income",
    "employment",
    "household",
    "racial_ethnic",
    "geography",
    "election",
]


@dataclass(frozen=True)
class FeatureGroup:
    """One thematic model group: its display title and member features."""

    title: str
    features: list[ModelVariable]


MODEL_GROUPS: dict[SlugGroupName, FeatureGroup] = {
    "language": FeatureGroup("Language", LANGUAGE_FEATURES),
    "citizenship": FeatureGroup(
        "US Citizenship and Residency Status", CITIZENSHIP_FEATURES
    ),
    "national_origin": FeatureGroup(
        "National Origin and Background", NATIONAL_ORIGIN_FEATURES
    ),
    "mobility": FeatureGroup("Mobility and Time in the U.S.", MOBILITY_FEATURES),
    "education": FeatureGroup("Education", EDUCATION_FEATURES),
    "income": FeatureGroup("Income and Affluence", INCOME_FEATURES),
    "employment": FeatureGroup("Employment and Industry", EMPLOYMENT_FEATURES),
    "household": FeatureGroup(
        "Household Structure (Age, Marriage, Sex)", HOUSEHOLD_FEATURES
    ),
    "racial_ethnic": FeatureGroup(
        "Racial and Ethnic Composition", RACIAL_ETHNIC_FEATURES
    ),
    "geography": FeatureGroup("Geography", [*GEOMETRY_FEATURES, *DHC_FEATURES]),
    "election": FeatureGroup("Elections", ELECTION_FEATURES),
}


# Variables a TRACT fit drops, so the build's schema and any model fit on
# tracts read one list rather than two that can drift. Two reasons, not
# one. HISPGROWTH and FBGROWTH have their prior-period ACS inputs at this
# level, but only for 62,522 of 85,395 tracts (73%): the 2011-2015
# five-year file is on 2010 tract boundaries, and a tract redrawn for 2020
# has no 2015 counterpart to grow from. Because the regression is
# complete-case on the whole matrix, admitting either one would drop the
# other 22,873 tracts out of every model, so they stay out until that
# trade is worth making deliberately.
#
# TURNOUT also has both its inputs, and is wrong rather than missing. The
# fault is the DENOMINATOR, not the votes: VOTINGAGEPOP comes from ACS
# five-year estimates, whose error on a single tract is large enough that
# 2,414 of 83,389 tracts report more votes cast than voting-age citizens,
# the worst by a factor of 16. The same denominator is fine at county
# level, where only 5 of 3,112 break 1.0. Measured on the GerryDB
# release's own per-tract counts, so no vote allocation of ours is
# involved -- California alone puts 205 tracts over 1.0.
TRACT_ABSENT_VARIABLES: tuple[str, ...] = (
    "HISPGROWTH",
    "FBGROWTH",
    "TURNOUT",
)


def _predictors(features: list[ModelVariable]) -> list[str]:
    """The predictor names among `features`, in declaration order."""
    return [f.var_name for f in features if f.role == "predictor"]


def _context_columns(slugs: Sequence[SlugGroupName] | None = None) -> list[str]:
    """Every declared context variable across the groups, sorted.

    Context variables (e.g. VOTINGAGEPOP, TURNOUT's denominator) are kept
    in processed.parquet for audit but never enter the model matrix.
    """
    groups = MODEL_GROUPS if slugs is None else {s: MODEL_GROUPS[s] for s in slugs}
    return sorted(
        f.var_name
        for group in groups.values()
        for f in group.features
        if f.role == "context"
    )


def all_model_features(exclude_variables: Sequence[str] = ()) -> list[str]:
    """Every predictor column, in group order -- the full model matrix.

    Parameters
    ----------
    exclude_variables : sequence of str
        Predictors to omit, for a level that lacks them; pass
        TRACT_ABSENT_VARIABLES to fit on tracts. Named variables that are
        not declared anywhere are refused, so a typo cannot silently
        leave the column in.

    Returns
    -------
    list of str
        The predictor names, in manifest order.

    Raises
    ------
    KeyError
        If a named variable is not declared in any model group.
    """
    _refuse_undeclared(exclude_variables)
    return [
        name
        for group in MODEL_GROUPS.values()
        for name in _predictors(group.features)
        if name not in exclude_variables
    ]


def _refuse_undeclared(variable_names: Sequence[str]) -> None:
    """Raise unless every name is a declared model variable.

    Parameters
    ----------
    variable_names : sequence of str
        The names a caller asked to exclude.

    Raises
    ------
    KeyError
        Naming the undeclared members, since excluding one would be a
        silent no-op.
    """
    declared = {f.var_name for g in MODEL_GROUPS.values() for f in g.features}
    undeclared = [name for name in variable_names if name not in declared]
    if undeclared:
        raise KeyError(
            f"cannot exclude undeclared variable(s) {undeclared}; they are not "
            "in any model group, so excluding them would be a no-op"
        )


def group_features(
    slugs: list[SlugGroupName], exclude_variables: Sequence[str] = ()
) -> list[str]:
    """The predictor columns of the selected groups, in order.

    `exclude_variables` drops the same names `all_model_features` does, so
    a per-group matrix and the full matrix agree about what a level has.
    """
    unknown = [s for s in slugs if s not in MODEL_GROUPS]
    if unknown:
        raise KeyError(f"unknown model group(s) {unknown}; known: {list(MODEL_GROUPS)}")
    _refuse_undeclared(exclude_variables)
    return [
        name
        for slug in slugs
        for name in _predictors(MODEL_GROUPS[slug].features)
        if name not in exclude_variables
    ]


# --- The processed.parquet schema --------------------------------------------
IDENTIFIERS: tuple[str, ...] = ("GEOID",)


def processed_columns(
    exclude_groups: Sequence[SlugGroupName] = (),
    exclude_variables: Sequence[str] = (),
) -> list[str]:
    """Every column of processed.parquet: identifiers, counts, targets,
    the model features, and the declared non-predictors (kept for audit).

    Parameters
    ----------
    exclude_groups : sequence of SlugGroupName
        Groups whose variables this level does not have at all -- the
        tract build passes ("election",), since presidential returns do
        not exist below county level. The PL counts and targets are
        never affected: every level derives those.
    exclude_variables : sequence of str
        Individual variables to omit, for when a level loses some of a
        group's members but not the group. Named variables that are not
        declared anywhere are refused, so a typo cannot silently leave
        the column in.

    Returns
    -------
    list of str
        The schema, in order.

    Raises
    ------
    KeyError
        If a named group does not exist, or a named variable is not
        declared in any group.
    """
    unknown = [slug for slug in exclude_groups if slug not in MODEL_GROUPS]
    if unknown:
        raise KeyError(f"unknown model group(s) {unknown}; known: {list(MODEL_GROUPS)}")
    _refuse_undeclared(exclude_variables)
    # Annotated: iterating the dict widens the Literal keys to str.
    kept: list[SlugGroupName] = [
        slug for slug in MODEL_GROUPS if slug not in exclude_groups
    ]
    dropped = set(exclude_variables)
    return [
        *IDENTIFIERS,
        *PL_COUNT_COLUMNS,
        *HISPANIC_RACE_COUNT_COLUMNS,
        *TARGETS,
        *(name for name in group_features(kept) if name not in dropped),
        *(name for name in _context_columns(kept) if name not in dropped),
    ]


# --- Import-time checks: refuse a manifest that contradicts itself -----------
_names = [f.var_name for g in MODEL_GROUPS.values() for f in g.features]
assert len(_names) == len(set(_names)), "a feature appears in more than one model group"
assert set(get_args(SlugGroupName)) == set(MODEL_GROUPS), (
    "GroupName drifted from MODEL_GROUPS"
)
_derived = {*PL_COUNT_COLUMNS, *HISPANIC_RACE_COUNT_COLUMNS, *TARGETS}
assert not _derived & set(_names), (
    f"derive-stage columns collide with feature names: {sorted(_derived & set(_names))}"
)
