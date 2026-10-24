"""Geometry features, attached from the TIGER/Line shapefile.

Geometry is downloaded whole (no variable-code fetch list to derive), so the
stage attaches these columns itself. The internal-point coordinates come
straight off the shapefile, and DENSITY is the PL total population over the
TIGER land area (ALAND), NaN where a unit has no land.
"""

from __future__ import annotations

from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
    Passthrough,
)
from build_dataset.ingest.pl.feats.total_pop_feats import TOTALPOP

# TIGER attribute columns referenced beyond their own declarations (the
# geometry fetch list, DENSITY's denominator), spelled exactly once. The
# coordinates double as var_names: the columns pass through unrenamed.
LAND_AREA = "ALAND"
INTERNAL_POINT_LATITUDE = "INTPTLAT"
INTERNAL_POINT_LONGITUDE = "INTPTLON"

GEOMETRY_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="TIGER",
        var_name=INTERNAL_POINT_LATITUDE,
        display_name="Latitude",
        description="Latitude of the unit's internal point (TIGER/Line 2020)",
        variable_computer=Passthrough(code=INTERNAL_POINT_LATITUDE),
    ),
    ModelVariable(
        source="TIGER",
        var_name=INTERNAL_POINT_LONGITUDE,
        display_name="Longitude",
        description="Longitude of the unit's internal point (TIGER/Line 2020)",
        variable_computer=Passthrough(code=INTERNAL_POINT_LONGITUDE),
    ),
    ModelVariable(
        source="TIGER",
        var_name="DENSITY",
        display_name="Population density",
        description="Population density: PL total population divided by TIGER "
        "land area (ALAND); rows with no land area are dropped",
        variable_computer=FractionalShare(
            numerator_codes=[TOTALPOP], denominator_codes=[LAND_AREA]
        ),
    ),
]
