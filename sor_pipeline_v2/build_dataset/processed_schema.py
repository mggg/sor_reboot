"""The processed.parquet schema: which columns the build saves, in order.

Assembled from imported pieces -- the derive stage's PL counts and targets,
and `model_groups`' predictors and context variables. `main_build` cuts the
derived frame to this list and refuses to save if any column is missing.
"""

from __future__ import annotations

from collections.abc import Sequence

from build_dataset.clean_and_derive.clean_and_derive_pl import (
    HISPANIC_RACE_COUNT_COLUMNS,
    PL_COUNT_COLUMNS,
    TARGETS,
)
from build_dataset.model_groups import (
    MODEL_GROUPS,
    ModelGroupName,
    context_columns,
    group_features,
    refuse_undeclared,
)

IDENTIFIERS: tuple[str, ...] = ("GEOID",)


def processed_columns(
    exclude_groups: Sequence[ModelGroupName] = (),
    exclude_variables: Sequence[str] = (),
) -> list[str]:
    """Every column of processed.parquet: identifiers, counts, targets,
    the model features, and the declared non-predictors (kept for audit).

    Parameters
    ----------
    exclude_groups : sequence of ModelGroupName
        Groups whose variables this level does not have at all. No
        current build passes any: the tract build drops individual
        variables instead (see `exclude_variables`). The PL counts and
        targets are never affected: every level derives those.
    exclude_variables : sequence of str
        Individual variables to omit, for when a level loses some of a
        group's members but not the group -- the tract build passes
        TRACT_ABSENT_VARIABLES. Named variables that are not
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
    refuse_undeclared(exclude_variables)
    # Annotated: iterating the dict widens the Literal keys to str.
    kept: list[ModelGroupName] = [
        slug for slug in MODEL_GROUPS if slug not in exclude_groups
    ]
    dropped = set(exclude_variables)
    return [
        *IDENTIFIERS,
        *PL_COUNT_COLUMNS,
        *HISPANIC_RACE_COUNT_COLUMNS,
        *TARGETS,
        *(name for name in group_features(kept) if name not in dropped),
        *(name for name in context_columns(kept) if name not in dropped),
    ]


# --- Import-time check: refuse a schema that names a column twice ------------
_names = [f.var_name for g in MODEL_GROUPS.values() for f in g.features]
_derived = {*PL_COUNT_COLUMNS, *HISPANIC_RACE_COUNT_COLUMNS, *TARGETS}
assert not _derived & set(
    _names
), f"derive-stage columns collide with feature names: {sorted(_derived & set(_names))}"
