"""Program to interact with the Archive API."""
from pathlib import Path
from typing import Set
from urllib.parse import urljoin

import requests as rq


class HoldingsAccessError(Exception):
    """Raised if response to an unsuccessful call to holdings endpoint."""


class FileUploadError(Exception):
    """Raised in response to the API returning a 500."""


class AuthenticationError(Exception):
    """Raised in response to the API refusing the access token."""


def call_holdings_endpoint(bodc_archive_url: str, deployment_id: str) -> dict:
    """Call endpoint to attempt to retrieve all held files for a deployment ID.

    Function will attempt to call the holdings endpoint, and then return
    a dict of files, to then be parsed by the 'parse_holdings' function.
    Function is also called from within 'parse_holdings'.

    Args:
        bodc_archive_url: The url for the archive, passed in from config file.
        deployment_id: The deployment_id of the file in question.

    Returns:
        The raw JSON response as a dict.
    """
    url = urljoin(bodc_archive_url, f"holdings/{deployment_id}")
    try:
        response = rq.get(url, timeout=600)
        response.raise_for_status()
        return response.json()
    except rq.exceptions.RequestException:
        raise HoldingsAccessError  # pylint: disable=W0707


def return_existing_glider_files(bodc_archive_url: str, deployment_id: str) -> Set[str]:
    """Return all filenames for a given deployment.

    Function first calls 'call_holdings_endpoint' to handle
    the initial call. If successful the parsing of the response
    takes place and the filenames are then parsed and returned
    as a set.

    Args:
        bodc_archive_url: The url for the archive, passed in from config file.
        deployment_id: The deployment_id of the file in question.

    Returns:
        A set of strings, with all the filenames for a deployment.
    """
    # Grab the raw response
    response = call_holdings_endpoint(bodc_archive_url, deployment_id)["files"]

    # Extract keys which contain the arrays of filenames
    keys_required = [file for file in response.keys() if (file.endswith("files") and "rxf" not in file)]

    # Build a master set to hold filenames
    all_filenames: Set[str] = set()

    # Iterate through each filetype, adding all filenames to master set
    for keys in keys_required:
        all_filenames = all_filenames | ({i["name"] for i in response[keys]})

    return all_filenames


def send_to_archive_api(file_location: Path, deployment_id: str, access_token: str, bodc_archive_url: str) -> str:
    """Send a file to the Archive API.

    The function constructs the URL needed for the API call, it then
    makes the call and sends the repsonse back to filepusher.py

    Args:
        file_location: used to build the relativepath and hostpath args.
        depoyment_id: Used to build part of the URL.
        access_token: Sent in the headers to the Archive API.
        bodc_archive_url: The url for the archive, passed in from config file.


    Returns:
        A string to inform the result of the API call.
    """
    url = urljoin(
        bodc_archive_url,
        f"archiveFile/{deployment_id}?"
        f"relativePath={file_location.name}&hostPath=/{file_location.parent.resolve()}/",
    )
    # Populate the headers with the access token
    headers = {"Authorization": f"Bearer {access_token}"}
    with open(
        file_location,
        "rb",
    ) as file:
        files = [
            (
                "data",
                (
                    file_location.name,
                    file.read(),
                    "multipart/form-data",
                ),
            )
        ]

    response = rq.request("POST", url, headers=headers, files=files, timeout=600)  # type: ignore

    if "500 Internal Server Error" in response.text:
        raise FileUploadError
    if "401 Unauthorized" in response.text:
        raise AuthenticationError
    if "File Archive Successful" in response.text:
        return "Success"
    return "Fail"
