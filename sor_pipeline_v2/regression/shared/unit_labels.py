"""What to call a row: GEOID -> a name a reader can place on a map.

A GEOID is the key the pipeline joins on, not something a figure title or
a residual table should print on its own. Counties carry a usable TIGER
name; tracts do not -- a tract's `NAME` is only its number, "44.02", which
says nothing without the county around it. So a tract is labelled with
the county it sits in, and both levels end with the state.

Shared by `explain` and `residual` so the same tract is spelled the same
way in a waterfall title and in a residual CSV.
"""

from __future__ import annotations

import pandas as pd

from build_dataset.ingest.geometry.geometry_api import (
    load_county_geometry,
    load_tract_geometry,
)
from utils import config
from utils.config import STATE_FIPS_TO_USPS


def load_unit_names(level: config.GeographicBuildLevel, geoids: pd.Series) -> pd.Series:
    """GEOID -> display name, for the units `geoids` actually contains.

    Tract geometry is published one state at a time, so the states are
    read off the GEOIDs rather than passed in: a run scoped to California
    reads one state's tracts, a national one reads every state that has a
    row. Each state's shapefile is downloaded once and cached, so the
    first national tract run pays for ~50 downloads and later ones do not.

    Parameters
    ----------
    level : config.GeographicBuildLevel
        Which dataset the GEOIDs come from. Decides their width (5 digits
        for counties, 11 for tracts) and which geometry source is read.
    geoids : pandas.Series
        The GEOIDs to label, as strings.

    Returns
    -------
    pandas.Series
        Indexed by GEOID, e.g. "Los Angeles County, CA" or "Census Tract
        44.02, Kern County, CA". A unit TIGER does not name keeps its
        GEOID as its label rather than going NaN, so a missing name
        cannot silently blank a figure title.
    """
    county_names = load_county_geometry().set_index("GEOID")["NAME"]
    if level == "national_counties":
        labels = county_names + " County"
    else:
        states = sorted({geoid[:2] for geoid in geoids})
        tract_names = pd.concat(
            [load_tract_geometry(state_fips) for state_fips in states]
        ).set_index("GEOID")["NAME"]
        parent_county = pd.Series(
            tract_names.index.str[:5], index=tract_names.index
        ).map(county_names)
        labels = "Census Tract " + tract_names + ", " + parent_county + " County"
    usps = pd.Series(labels.index.str[:2], index=labels.index).map(STATE_FIPS_TO_USPS)
    return (labels + ", " + usps).fillna(pd.Series(labels.index, index=labels.index))


def unit_label(geoid: str, unit_names: pd.Series) -> str:
    """One row's figure title: its name and the GEOID it was joined on."""
    return f"{unit_names.get(geoid, geoid)} (GEOID {geoid})"
