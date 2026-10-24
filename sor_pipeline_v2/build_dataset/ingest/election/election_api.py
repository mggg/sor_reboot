"""APIs for loading the election source file (a local CSV, nothing fetched).

County only. MEDSL publishes counties and stops, because precincts do
not nest in tracts and so no canvass is reported by tract. The tract
build gets its returns elsewhere -- from the lab's GerryDB release, read
by `tract_election_api` -- and the two paths share no code and no source
file, which is what makes MEDSL an independent check on it
(`data_audit.scripts.reconcile_tract_election`).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from build_dataset.ingest.election.election_feats import (
    DEM_VOTES,
    DEM_VOTES_2016,
    REP_VOTES,
    REP_VOTES_2016,
)
from utils.config import RAW_NATIONAL_DIR

# MIT Election Data + Science Lab county presidential returns, downloaded
# from Harvard Dataverse (doi:10.7910/DVN/VOQCHQ) -- an independent
# compilation of official state canvasses. The download is guestbook-gated
# (MEDSL tracks usage), so it cannot be fetched unattended; instead the
# local copy is verified against the checksum Dataverse publishes in its
# open metadata API (api/datasets/:persistentId), pinned here.
MEDSL_COUNTY_RAW_CSV = "countypres_2000-2024.csv"
# The byte checksum of the original CSV, from the metadata API -- what the
# load-time gate verifies. (The dataset PAGE shows tabular files under
# their UNF -- "UNF:6:VKZJHPbIwGBnmWCslEFbtw==" -- Dataverse's semantic
# fingerprint of the normalized data. It cannot be recomputed from the
# raw CSV without replicating Dataverse's ingest, so it is recorded here
# as provenance, not enforced.)
MEDSL_COUNTY_RAW_MD5 = "bd6661282936006b4ef4f5ee71418f3e"

# (year, MEDSL party) -> the pipeline's column name. This dict is also the
# extraction's scope: the loader keeps exactly these years and parties.
MEDSL_COLUMN_NAMES: dict[tuple[int, str], str] = {
    (2020, "DEMOCRAT"): DEM_VOTES,
    (2020, "REPUBLICAN"): REP_VOTES,
    (2016, "DEMOCRAT"): DEM_VOTES_2016,
    (2016, "REPUBLICAN"): REP_VOTES_2016,
}

# Kansas City reports separately from its counties; census geography (and
# therefore this pipeline's spine) folds it into Jackson County, MO.
KANSAS_CITY_PSEUDO_FIPS = "2938000"
JACKSON_COUNTY_MO_GEOID = "29095"

# Bedford City, VA merged into Bedford County in 2013, but MEDSL carries a
# vestigial 2016 row for it with zero votes. It is not on the 2020 census
# spine; dropped so the loader emits only real 2020-vintage counties.
BEDFORD_CITY_VA_DEFUNCT = "51515"


def _check_medsl_county_raw_md5(medsl_path: Path) -> None:
    """Check that the local MEDSL county returns CSV matches the published MD5 checksum.

    Parameters
    ----------
    medsl_path : Path
        Location of the downloaded MEDSL CSV.

    Raises
    ------
    ValueError
        If the file's MD5 differs from the checksum Dataverse publishes --
        the file was modified or is a different dataset version.
    FileNotFoundError
        If the file is absent from the raw data directory.
    """
    file_md5 = hashlib.md5(medsl_path.read_bytes()).hexdigest()
    if file_md5 != MEDSL_COUNTY_RAW_MD5:
        raise ValueError(
            f"{medsl_path.name}: md5 {file_md5} does not match the published "
            f"Dataverse checksum {MEDSL_COUNTY_RAW_MD5} -- the file was "
            "modified or is a different version; re-download from "
            "doi:10.7910/DVN/VOQCHQ."
        )


def _repair_and_drop_non_county_rows(election_df: pd.DataFrame) -> pd.DataFrame:
    """Repair known anomalies and drop non-county rows from the election DataFrame.

    Parameters
    ----------
    election_df : pandas.DataFrame
        Filtered MEDSL rows with a string `county_fips` column.

    Returns
    -------
    pandas.DataFrame
        The same rows with a five-digit `GEOID` column added; FIPS-less
        reporting units, Alaska, and the defunct Bedford City, VA dropped;
        and Kansas City's pseudo-FIPS folded into Jackson County, MO.
    """
    election_df = election_df.dropna(subset=["county_fips"])
    election_df["GEOID"] = election_df["county_fips"].str.zfill(5)
    election_df.loc[election_df["GEOID"] == KANSAS_CITY_PSEUDO_FIPS, "GEOID"] = (
        JACKSON_COUNTY_MO_GEOID
    )
    election_df = election_df[election_df["state_po"] != "AK"]
    election_df = election_df[election_df["GEOID"] != BEDFORD_CITY_VA_DEFUNCT]
    return election_df


def _calculate_vote_totals(election_df: pd.DataFrame) -> pd.DataFrame:
    """One vote count per (county, year, party), respecting TOTAL rows.

    States report one of two ways: a single TOTAL row per county-party, or
    the same votes split across mode rows (early / absentee / election
    day) -- and a county-party can have both. Where a TOTAL row exists it
    already contains the split rows, so summing everything would
    double-count; TOTAL wins, and only groups without one sum their modes.

    Parameters
    ----------
    election_df : pandas.DataFrame
        Cleaned MEDSL rows (one per county-year-party-mode) with GEOID,
        year, party, mode, and candidatevotes columns.

    Returns
    -------
    pandas.DataFrame
        One row per GEOID with the four vote columns named by
        MEDSL_COLUMN_NAMES, in its declaration order.

    Raises
    ------
    KeyError
        If a (year, party) pair from MEDSL_COLUMN_NAMES is absent from the
        data -- the pair is named in the error.
    """
    group_keys = ["GEOID", "year", "party"]
    is_total_row = election_df["mode"] == "TOTAL"
    group_has_total = is_total_row.groupby(
        [election_df[key] for key in group_keys]
    ).transform("any")
    counted_rows = election_df[is_total_row | ~group_has_total]

    votes_by_year_party = (
        counted_rows.groupby(group_keys)["candidatevotes"]
        .sum()
        .unstack(["year", "party"])
    )
    # Flatten the (year, party) column MultiIndex to the pipeline names by
    # selecting through the scope dict -- which also asserts all four
    # columns arrived (a missing year/party raises KeyError by name) and
    # fixes the output column order to the dict's declaration order.
    county_votes = pd.DataFrame(
        {
            column_name: votes_by_year_party[year_party]
            for year_party, column_name in MEDSL_COLUMN_NAMES.items()
        }
    )
    return county_votes.reset_index()


def load_county_election() -> pd.DataFrame:
    """MEDSL county returns -> one row per GEOID, four vote columns.

    Extracts the two-party presidential vote for 2020 and 2016. The
    handling below was verified against the file for both years:

    - Rows with no FIPS are non-county reporting units (statewide
      write-ins, overseas/UOCAVA ballots, RI's federal precinct); dropped.
    - Kansas City's separate return (pseudo-FIPS 2938000, present in both
      years) is folded into Jackson County.
    - Where a county-party has a TOTAL row it is authoritative and the
      mode-split rows would double-count, so TOTAL wins; otherwise modes
      are summed. (2016 is all-TOTAL; 2020 mixes both styles.)
    - Alaska is excluded: MEDSL reports its election districts, which do
      not map to the census boroughs on the spine. AK boroughs therefore
      get NaN votes after the merge, like Puerto Rico.

    Returns
    -------
    pandas.DataFrame
        One row per county: GEOID plus Democratic and Republican
        presidential votes for 2020 and 2016 (floats).

    Raises
    ------
    ValueError
        If the source CSV fails its published-checksum verification.
    FileNotFoundError
        If the source CSV is absent from the raw data directory.
    KeyError
        If a required (year, party) combination is missing from the file.
    """
    medsl_path = RAW_NATIONAL_DIR / MEDSL_COUNTY_RAW_CSV

    _check_medsl_county_raw_md5(medsl_path)

    medsl_pres_data = pd.read_csv(medsl_path, dtype={"county_fips": "string"})
    election_df = medsl_pres_data[
        medsl_pres_data["year"].isin({year for year, _ in MEDSL_COLUMN_NAMES})
        & (medsl_pres_data["office"] == "US PRESIDENT")
        & medsl_pres_data["party"].isin({party for _, party in MEDSL_COLUMN_NAMES})
    ].copy()

    election_df = _repair_and_drop_non_county_rows(election_df)

    return _calculate_vote_totals(election_df)


if __name__ == "__main__":
    print(load_county_election().head())
