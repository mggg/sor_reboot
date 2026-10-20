"""What a report group names: the model's groups, plus population views.

The regression partitions the PREDICTORS into thematic groups, and that
partition is the manifest's job. It says nothing about the other half of
the processed schema -- the decennial counts, the race-choice shares, the
classification columns -- because no model fits on them. They are still
the columns the project is actually about, so the report needs names for
them too.

These are reporting views, not model structure, which is why they live
here and not in the manifest. Each is derived from a manifest constant
rather than listed by hand, so a column added to the schema cannot go
missing from the report. `check_coverage` is what enforces that.

The manifest's own TARGETS constant lumps three families together; they
are split apart here because they answer different questions. A share OF
THE HISPANIC POPULATION is the modelled outcome. The matching share OF
THE TOTAL POPULATION is a different quantity that moves with how
Hispanic a place is, not with how its Hispanic residents answered.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, cast

from build_dataset.feature_manifest import (
    HISPANIC_RACE_COUNT_COLUMNS,
    IDENTIFIERS,
    MODEL_GROUPS,
    PL_COUNT_COLUMNS,
    TARGETS,
    SlugGroupName,
    all_model_features,
    group_features,
    processed_columns,
)

# The groups this package adds on top of the model's own. A Literal
# rather than bare str so a typo is a type error, not a runtime one, and
# so the dict below cannot gain a key nobody can name.
PopulationGroupName = Literal[
    "counts",
    "share_of_hisp",
    "share_of_pop",
    "dominant_choice",
    "context",
]
# What `--groups` accepts: a model group or a population group.
ReportGroupName = SlugGroupName | PopulationGroupName

OF_HISP_SUFFIX = "_Pct_of_Hisp_Pop"
OF_TOTAL_SUFFIX = "_Pct_of_Total_Pop"

# The context column the ACS declares with role="context": a denominator
# the clean stage uses, carried into the schema for audit.
CONTEXT_COLUMNS: tuple[str, ...] = ("VOTINGAGEPOP",)

POPULATION_GROUPS: dict[PopulationGroupName, tuple[str, ...]] = {
    # Head counts straight from the decennial file, Hispanic-by-race
    # included. TOTALPOP and HISPANIC live here.
    "counts": tuple(PL_COUNT_COLUMNS) + tuple(HISPANIC_RACE_COUNT_COLUMNS),
    # The modelled outcomes: of the Hispanic residents here, what share
    # chose this race?
    "share_of_hisp": tuple(t for t in TARGETS if t.endswith(OF_HISP_SUFFIX)),
    # The same numerators over the WHOLE population. Not outcomes: these
    # rise and fall with Hispanic share of the place.
    "share_of_pop": tuple(t for t in TARGETS if t.endswith(OF_TOTAL_SUFFIX)),
    # Which race choice is the largest, as a label and as indicators.
    "dominant_choice": tuple(
        t for t in TARGETS if not t.endswith((OF_HISP_SUFFIX, OF_TOTAL_SUFFIX))
    ),
    "context": CONTEXT_COLUMNS,
}


def known_groups() -> list[str]:
    """Every group name the report accepts, model groups first."""
    return [*MODEL_GROUPS, *POPULATION_GROUPS]


def validated_group_names(names: Sequence[str]) -> list[ReportGroupName]:
    """Group names from outside, checked and narrowed.

    The boundary where strings become names: argparse hands over
    `list[str]`, and everything downstream wants to know it is holding
    real group names. Call this once, at the edge.

    Parameters
    ----------
    names : sequence of str
        Group names as supplied, model or population.

    Returns
    -------
    list of ReportGroupName
        The same names, narrowed. A command-line string cannot carry the
        Literal type, so the membership check is what earns the cast.

    Raises
    ------
    KeyError
        Naming every unrecognised group, with the known ones listed.
    """
    unknown = [name for name in names if name not in set(known_groups())]
    if unknown:
        raise KeyError(f"unknown group(s) {unknown}; known: {known_groups()}")
    return [cast(ReportGroupName, name) for name in names]


def model_slugs(names: Sequence[ReportGroupName]) -> list[SlugGroupName]:
    """Just the model-group slugs from a mixed request, narrowed.

    Parameters
    ----------
    names : sequence of ReportGroupName
        Group names, already validated.

    Returns
    -------
    list of SlugGroupName
        The members that are model groups. The cast narrows the union to
        its model half, which the filter has just established.
    """
    return [cast(SlugGroupName, name) for name in names if name in MODEL_GROUPS]


def resolve_columns(
    names: Sequence[ReportGroupName], exclude_variables: Sequence[str] = ()
) -> list[str]:
    """The columns a request names, in request order, without repeats.

    Parameters
    ----------
    names : sequence of ReportGroupName
        Group names, model or population, already validated by
        `validated_group_names`.
    exclude_variables : sequence of str
        Predictors this level does not have; population groups are
        unaffected, being counts and derived shares every level has.

    Returns
    -------
    list of str
        Column names.
    """
    ordered: list[str] = []
    for name in names:
        # The casts split the union by hand: `in MODEL_GROUPS` is a plain
        # membership test, which narrows nothing for the type checker,
        # and a model group's columns depend on the level's exclusions
        # while a population group's are a fixed tuple.
        if name in MODEL_GROUPS:
            columns: Sequence[str] = group_features(
                [cast(SlugGroupName, name)], exclude_variables
            )
        else:
            columns = POPULATION_GROUPS[cast(PopulationGroupName, name)]
        ordered.extend(column for column in columns if column not in ordered)
    return ordered


def check_coverage(exclude_variables: Sequence[str] = ()) -> list[str]:
    """Processed columns no report group names -- empty when all are covered.

    The report is only trustworthy as an inventory if every column in the
    schema is reachable through some group. A column added to the
    manifest without a home here shows up in this list.

    Parameters
    ----------
    exclude_variables : sequence of str
        Predictors this level does not have.

    Returns
    -------
    list of str
        The orphans, in schema order.
    """
    reachable = set(all_model_features(exclude_variables))
    for columns in POPULATION_GROUPS.values():
        reachable.update(columns)
    return [
        column
        for column in processed_columns(exclude_variables=exclude_variables)
        if column not in reachable and column not in IDENTIFIERS
    ]
