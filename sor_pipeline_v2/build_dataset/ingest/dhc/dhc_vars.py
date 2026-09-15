"""What the DHC source declares: the urban/rural feature and its codes.

Urban/rural is not in the PL redistricting file and the ACS does not measure it
at all; it lives in the 2020 Demographic and Housing Characteristics file,
table P2. Complete count, so no margins of error and no reliability filtering.

Only the urban share is modeled. Verified across all 3,221 counties:
P2_002N + P2_003N == P2_001N exactly and P2_004N is always 0, so a rural share
would be `1 - URBANSHARE` -- a perfectly collinear duplicate that would split
importance across two identical columns. Same reasoning as omitting
renter-occupied alongside HISPOWNEROCC in the ACS spec.

URBANSHARE is distinct from DENSITY (see `geometry/`), which is a county-wide
average: a large county can be low-density overall while nearly all its
residents live in one town.
"""

from __future__ import annotations

# (feature name, numerator code, denominator code, meaning)
DHC_FEATURES: tuple[tuple[str, str, str, str], ...] = (
    ("URBANSHARE", "P2_002N", "P2_001N",
     "Share of the county's total population living in an urban area "
     "(2020 Census urban/rural classification)"),
)

# P2_003N is requested only to re-verify the collinearity note in the module
# docstring (P2_002N + P2_003N == P2_001N), not to build a feature.
DHC_CODES: tuple[str, ...] = ("P2_001N", "P2_002N", "P2_003N")

# Every code the DHC features are defined over must actually be requested.
assert {c for _n, num, den, _m in DHC_FEATURES for c in (num, den)} <= set(DHC_CODES)

# DHC's table P2 (urban/rural) shares code NAMES with the PL file's table P2
# (Hispanic by race) -- P2_002N means "urban population" here and "Hispanic
# population" there. The fetch prefixes DHC columns so the two surveys cannot
# collide in the merged dataset; the clean stage reads `DHC_COLUMN_PREFIX + code`.
DHC_COLUMN_PREFIX = "DHC_"
