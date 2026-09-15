import pandas as pd

from build_dataset.ingest.acs import acs_spec
from build_dataset.ingest.census_client import ACS5_PRIOR_URL, ACS5_URL, get_census_data


def fetch_acs_features(for_geo: str, in_geo: str) -> pd.DataFrame:
    """All 350 spec columns (estimates + MOEs), 2016-2020 vintage."""
    return get_census_data(ACS5_URL, acs_spec.all_codes(), for_geo, in_geo)


def fetch_acs_prior(for_geo: str, in_geo: str) -> pd.DataFrame:
    """The 2 growth-feature codes from the 2011-2015 vintage.

    Columns come back suffixed (see `acs_spec.PRIOR_SUFFIX`): the prior vintage
    publishes the same code names as 2016-2020, and unsuffixed they would
    collide with `fetch_acs_features` columns in the merged dataset.
    """
    df = get_census_data(ACS5_PRIOR_URL, list(acs_spec.PRIOR_CODES), for_geo, in_geo)
    return df.rename(
        columns={code: code + acs_spec.PRIOR_SUFFIX for code in acs_spec.PRIOR_CODES}
    )
