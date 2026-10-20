"""The audit's shared findings vocabulary.

Every comparison script (census website vs raw, election source vs raw)
emits the same record shape with the same verdict set, so all findings
CSVs stay uniform and greppable across the audit.
"""

from dataclasses import dataclass
from enum import StrEnum

import pandas as pd


class FindingStatus(StrEnum):
    """The verdicts a comparison can reach."""

    MATCH = "match"
    MISMATCH = "MISMATCH"
    BOTH_MISSING = "both_missing"
    SUPPRESSION_MATCH = "suppression_match"
    # A small numeric difference consistent with the two channels' known
    # methodology gap (e.g. DRA's block allocation vs certified county
    # totals) -- agreement, with the delta recorded.
    ALLOCATION_DELTA = "allocation_delta"
    NEEDS_REVIEW = "needs_review"
    ROW_ABSENT = "row_absent"


@dataclass(frozen=True)
class AuditFinding:
    """One (table, code, county) comparison -- one row of a findings CSV.

    The website_* fields hold the reference channel's code and value --
    the census website for the table comparisons, the source CSV for the
    election comparison.
    """

    table: str
    website_code: str
    raw_column: str
    geoid: str
    county: str
    website_value: str
    raw_value: str
    status: FindingStatus
    # Signed numeric difference (raw side minus reference side) where a
    # comparison is quantitative and inexact; empty for exact statuses.
    delta: str = ""


def to_number(value: object) -> float | None:
    """A float if the value is numeric, else None. Strips the thousands
    commas and MOE plus-minus the census website adds to some cells.

    `object`, not str: raw values arrive via DataFrame.at, which the
    pandas stubs type as Scalar (str | bytes | float | ...). This function
    truly accepts anything -- it str()s whatever it gets.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    cleaned = str(value).strip().replace(",", "").removeprefix("±")
    try:
        return float(cleaned)
    except ValueError:
        return None
