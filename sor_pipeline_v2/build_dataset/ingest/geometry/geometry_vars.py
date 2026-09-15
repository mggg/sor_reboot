"""What the geometry source declares: the gazetteer features. Model group J.

The three modeled features are ATTRIBUTES of the TIGER/Line file, not census
tabulations: the internal-point coordinates come straight off the shapefile,
and DENSITY is derived in the clean stage as the PL total population over the
TIGER land area (ALAND), with zero-land rows dropped.
"""

from __future__ import annotations

# (feature name, meaning)
GEOMETRY_FEATURES: tuple[tuple[str, str], ...] = (
    ("INTPTLAT",
     "Latitude of the county's internal point (TIGER/Line 2020)"),
    ("INTPTLON",
     "Longitude of the county's internal point (TIGER/Line 2020)"),
    ("DENSITY",
     "Population density: PL total population divided by TIGER land area "
     "(ALAND); rows with no land area are dropped"),
)
