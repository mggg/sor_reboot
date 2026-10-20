"""Harvard Dataverse: resolve a deposit's files, and fetch one verified.

Two of this pipeline's sources are Dataverse deposits -- VEST's 2020
precinct archives (doi:10.7910/DVN/K7760H) and MEDSL's county returns
(doi:10.7910/DVN/VOQCHQ) -- and the repository's protocol is the same for
both: a DOI names a deposit, an open metadata API lists its files with
their ids and published digests, and a file is downloaded by its numeric
id rather than by name.

What stays with the caller: which filename it wants (a naming convention
is the depositor's, not Dataverse's), where the bytes are cached, and
what is done with them.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import requests

DATAVERSE_DATASET_API = "https://dataverse.harvard.edu/api/datasets/:persistentId/"
DATAVERSE_FILE_API = "https://dataverse.harvard.edu/api/access/datafile/{file_id}"
DATAVERSE_HEADERS = {
    "User-Agent": "sor-pipeline (research use)"
}  # GET /api/datasets/:persistentId/ wants a non default User-Agent.

METADATA_TIMEOUT_SECONDS = 60
DOWNLOAD_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class PublishedArchive:
    """One Dataverse file: where to get it and the digest it should have."""

    filename: str
    file_id: int
    published_md5: str
    dataset_version: str


def _latest_version(doi: str) -> dict:
    """The deposit's current published version, as Dataverse reports it.

    Parameters
    ----------
    doi : str
        The deposit's persistent id, e.g. "doi:10.7910/DVN/K7760H".

    Returns
    -------
    dict
        The `latestVersion` object: its number, and its file listing.

    Raises
    ------
    ValueError
        If Dataverse answers with anything but 200.
    requests.RequestException
        Propagated on network failure.
    """
    response = requests.get(
        DATAVERSE_DATASET_API,
        params={"persistentId": doi},
        headers=DATAVERSE_HEADERS,
        timeout=METADATA_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise ValueError(
            f"Dataverse returned {response.status_code} for {doi}: "
            f"{response.text[:200]}"
        )
    return response.json()["data"]["latestVersion"]


def published_archive(
    doi: str, filename: str, absent_hint: str = ""
) -> PublishedArchive:
    """Look up one named file in a deposit's listing.

    The file id is resolved at run time rather than pinned, so a version
    bump cannot leave a stale id silently pointing at the wrong release;
    the published MD5 comes back with it and is what the download is
    checked against.

    Parameters
    ----------
    doi : str
        The deposit's persistent id.
    filename : str
        The file to find, exactly as the deposit names it.
    absent_hint : str
        Appended to the error when the deposit lists no such file -- the
        caller's interpretation of what a miss means, which Dataverse
        cannot know.

    Returns
    -------
    PublishedArchive
        The file's name, Dataverse id, published MD5, and the dataset
        version those came from.

    Raises
    ------
    ValueError
        If Dataverse answers with an error, or lists no such file.
    requests.RequestException
        Propagated on network failure.
    """
    version = _latest_version(doi)
    label = f"{version.get('versionNumber')}.{version.get('versionMinorNumber')}"
    for entry in version["files"]:
        data_file = entry["dataFile"]
        if data_file["filename"] == filename:
            return PublishedArchive(
                filename=filename,
                file_id=int(data_file["id"]),
                published_md5=str(data_file["md5"]),
                dataset_version=label,
            )
    raise ValueError(
        f"{doi} (version {label}) lists no file named {filename}"
        + (f"; {absent_hint}" if absent_hint else "")
    )


def download_verified(archive: PublishedArchive) -> bytes:
    """Download a file by id, checked against the digest Dataverse publishes.

    Parameters
    ----------
    archive : PublishedArchive
        As returned by `published_archive`.

    Returns
    -------
    bytes
        The file's contents, digest confirmed.

    Raises
    ------
    ValueError
        If the downloaded bytes do not match the MD5 Dataverse publishes.
    requests.RequestException
        Propagated on network failure.
    """
    url = DATAVERSE_FILE_API.format(file_id=archive.file_id)
    payload = requests.get(
        url, headers=DATAVERSE_HEADERS, timeout=DOWNLOAD_TIMEOUT_SECONDS
    ).content
    digest = hashlib.md5(payload).hexdigest()
    if digest != archive.published_md5:
        raise ValueError(
            f"{archive.filename}: md5 {digest} does not match the checksum "
            f"Dataverse publishes ({archive.published_md5}) for dataset version "
            f"{archive.dataset_version}; refusing to cache an unverified file."
        )
    return payload
