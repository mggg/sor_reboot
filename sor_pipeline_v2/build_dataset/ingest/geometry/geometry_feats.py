"""Geometry features, attached from the TIGER/Line shapefile.

All three are custom: geometry is downloaded whole (no variable-code fetch
list to derive), so the stage attaches these columns itself. The
internal-point coordinates come straight off the shapefile, and DENSITY is
the PL total population over the TIGER land area (ALAND), with zero-land
rows dropped.
"""

from __future__ import annotations

from build_dataset.ingest.feature_utils import ModelFeature

GEOMETRY_FEATURES: list[ModelFeature] = [
    ModelFeature(
        source_table="TIGER",
        table_code=None,
        var_name="INTPTLAT",
        description="Latitude of the county's internal point (TIGER/Line 2020)",
        custom=True,
    ),
    ModelFeature(
        source_table="TIGER",
        table_code=None,
        var_name="INTPTLON",
        description="Longitude of the county's internal point (TIGER/Line 2020)",
        custom=True,
    ),
    ModelFeature(
        source_table="TIGER",
        table_code=None,
        var_name="DENSITY",
        description="Population density: PL total population divided by TIGER "
        "land area (ALAND); rows with no land area are dropped",
        custom=True,
    ),
]
