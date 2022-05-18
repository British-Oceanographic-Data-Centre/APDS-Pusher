"""Program to interact with the Archive API."""
from pathlib import Path
from typing import Set

import requests as rq


class HoldingsAccessError(Exception):
    """Exception raised if unable to make call to holdings endpoint."""


class FileUploadError(Exception):
    """Raised in response to the API returning a 500."""


class AuthenticationError(Exception):
    """Raised in response to the API refusign the access token."""


def call_holdings_endpoint(deployment_id: str) -> dict:
    """Call endpoint to attempt to retrieve all held files for a deployment ID.

    Function will attempt to call the holdings endpoint, and then return
    a dict of files, to then be parsed by the 'parse_holdings' function.
    Function is also called from within 'parse_holdings'.

    Args:
        deployment_id: The deployment_id of the file in question.

    Returns:
        The raw JSON response as a dict.
    """
    url = f"https://api.linked-systems.uk/api/meta/v2/holdings/{deployment_id}"
    try:
        response = rq.get(url)
        response.raise_for_status()
        return response.json()
    except rq.exceptions.RequestException:
        raise HoldingsAccessError from None


def return_existing_glider_files(deployment_id: str) -> Set[str]:
    """Return all filenames for a given deployment.

    Function first calls 'call_holdings_endpoint' to handle
    the initial call. If successful the parsing of the response
    takes place and the filenames are then parsed and returned
    as a set.

    Returns:
        A set of strings, with all the filenames for a deployment.
    """
    # Grab the raw response
    response = call_holdings_endpoint(deployment_id)["files"]

    # Extract keys which contain the arrays of filenames
    keys_required = [file for file in response.keys() if file.endswith("files")]

    # Build a master set to hold filenames
    all_filenames: Set[str] = set()

    # Iterate through each filetype, adding all filenames to master set
    for keys in keys_required:
        all_filenames = all_filenames | ({i["name"] for i in response[keys]})

    return all_filenames


def send_to_archive_api(file_location: Path, deployment_id: str, access_token: str) -> str:
    """Send a file to the Archive API.

    The function constructs the URL needed for the API call, it then
    makes the call and sends the repsonse back to filepusher.py

    Args:
        file_location: used to build the relativepath and hostpath args.
        depoyment_id: Used to build part of the URL.
        access_token: Sent in the headers to the Archive API.

    Returns:
        A string to inform the result of the API call.
    """
    # Construct relative path for API string, then poplulate template string
    relative_path = f"{file_location.parent.name}/{file_location.name}"
    base_url = "https://api.linked-systems.uk/api/meta/v2/archiveFile/{}?relativePath={}&hostPath=/{}/"
    url_to_post = base_url.format(deployment_id, relative_path, file_location.name)

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

    response = rq.request("POST", url_to_post, headers=headers, files=files)  # type: ignore

    if "500 Internal Server Error" in response.text:
        raise FileUploadError
    if "401 Unauthorized" in response.text:
        raise AuthenticationError
    if "File Archive Successful" in response.text:
        return "Success"
    return "Fail"
