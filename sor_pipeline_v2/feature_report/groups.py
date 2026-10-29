"""Which columns a feature report can describe, named by group.

A report describes predictors one model group at a time -- the groups the
regression is built from, in `model_groups` -- and each group brings its
context variables with it (citizenship brings VOTINGAGEPOP). The one other
name a report accepts is "targets": the four shares the regression
predicts, so their distributions can be read next to the predictors'.

Nothing else in processed.parquet is reported. The PL counts, the shares
of the total population and the dominant-choice classification feed no
model, and their distributions mostly restate how large or how Hispanic a
place is.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, cast

from build_dataset.model_groups import (
    MODEL_GROUPS,
    ModelGroupName,
    context_columns,
    group_features,
)
from regression.shared.run_config import REGRESSION_TARGETS

ReportGroupName = ModelGroupName | Literal["targets"]


def known_groups() -> list[str]:
    """Every group name the report accepts, model groups first."""
    return [*MODEL_GROUPS, "targets"]


def validated_group_names(names: Sequence[str]) -> list[ReportGroupName]:
    """Group names from outside, checked and narrowed.

    The boundary where strings become names: argparse hands over
    `list[str]`, and everything downstream wants to know it is holding
    real group names. Call this once, at the edge.

    Parameters
    ----------
    names : sequence of str
        Group names as supplied: model groups, or "targets".

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


def model_group_names(names: Sequence[ReportGroupName]) -> list[ModelGroupName]:
    """Just the model groups from a request, without "targets".

    Parameters
    ----------
    names : sequence of ReportGroupName
        Group names, already validated.

    Returns
    -------
    list of ModelGroupName
        The members that are model groups.
    """
    return [name for name in names if name != "targets"]


def resolve_columns(
    names: Sequence[ReportGroupName], exclude_variables: Sequence[str] = ()
) -> list[str]:
    """The columns a request names, in request order, without repeats.

    Parameters
    ----------
    names : sequence of ReportGroupName
        Group names, already validated by `validated_group_names`.
    exclude_variables : sequence of str
        Predictors this level does not have; the targets are unaffected,
        since every level has them.

    Returns
    -------
    list of str
        Column names: a model group's predictors then its context
        variables, or the four targets.
    """
    ordered: list[str] = []
    for name in names:
        if name == "targets":
            columns = list(REGRESSION_TARGETS)
        else:
            columns = [
                *group_features([name], exclude_variables),
                *(
                    column
                    for column in context_columns([name])
                    if column not in exclude_variables
                ),
            ]
        ordered.extend(column for column in columns if column not in ordered)
    return ordered
