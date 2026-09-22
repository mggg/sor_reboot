"""Which declared columns the models fit on, and how they group.

The feats packages declare every column ingest produces, and the derive stage
declares the columns it creates (counts and targets, next to the code that
makes them). This module owns only the two judgments nobody else can make:
which declared columns are PREDICTORS, and how the predictors partition into
thematic groups. It assembles the processed.parquet schema from those
imported pieces.

The import arrow points one way: the manifest imports from the sources and
the derive stage; neither knows the manifest exists.
"""

from __future__ import annotations

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
from build_dataset.ingest.dhc.dhc_feats import DHC_FEATURES
from build_dataset.ingest.election.election_feats import ELECTION_FEATURES
from build_dataset.ingest.feature_utils import ModelFeature
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
    features: list[ModelFeature]


# Declared (in citizenship_feats, so the ACS fetch requests it) but never a
# predictor: it is TURNOUT's denominator and nothing else.
NOT_PREDICTORS: frozenset[str] = frozenset({"VOTINGAGEPOP"})

# URBANSHARE sits with geography: like DENSITY it describes the place, not
# its Hispanic residents.
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


def _predictors(features: list[ModelFeature]) -> list[str]:
    """The predictor names among `features`, in declaration order."""
    return [f.var_name for f in features if f.var_name not in NOT_PREDICTORS]


def all_model_features() -> list[str]:
    """Every predictor column, in group order -- the full model matrix."""
    return [
        name for group in MODEL_GROUPS.values() for name in _predictors(group.features)
    ]


def group_features(slugs: list[str]) -> list[str]:
    """The predictor columns of the selected groups, in order."""
    unknown = [s for s in slugs if s not in MODEL_GROUPS]
    if unknown:
        raise KeyError(f"unknown model group(s) {unknown}; known: {list(MODEL_GROUPS)}")
    return [name for slug in slugs for name in _predictors(MODEL_GROUPS[slug].features)]


# --- The processed.parquet schema --------------------------------------------
IDENTIFIERS: tuple[str, ...] = ("GEOID",)


def processed_columns() -> list[str]:
    """Every column of processed.parquet: identifiers, counts, targets,
    the model features, and the declared non-predictors (kept for audit)."""
    return [
        *IDENTIFIERS,
        *PL_COUNT_COLUMNS,
        *HISPANIC_RACE_COUNT_COLUMNS,
        *TARGETS,
        *all_model_features(),
        *sorted(NOT_PREDICTORS),
    ]


# --- Import-time checks: refuse a manifest that contradicts itself -----------
_names = [f.var_name for g in MODEL_GROUPS.values() for f in g.features]
assert len(_names) == len(set(_names)), "a feature appears in more than one model group"
assert set(get_args(SlugGroupName)) == set(
    MODEL_GROUPS
), "GroupName drifted from MODEL_GROUPS"
assert NOT_PREDICTORS <= set(_names), "NOT_PREDICTORS names an undeclared feature"
_derived = {*PL_COUNT_COLUMNS, *HISPANIC_RACE_COUNT_COLUMNS, *TARGETS}
assert not _derived & set(
    _names
), f"derive-stage columns collide with feature names: {sorted(_derived & set(_names))}"
