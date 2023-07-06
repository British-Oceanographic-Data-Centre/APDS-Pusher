"""Methods to deal with getting and displaying version info."""
from importlib.metadata import version as importlib_version

import requests


def get_github_tag_info() -> str:
    """Gets the newest tag from GitHub.

    Returns:
        str: The name of the latest tag.
    """
    tags = requests.get(
        "https://api.github.com/repos/British-Oceanographic-Data-Centre/APDS-Pusher/tags",
        timeout=60,
    ).json()
    latest = tags[0]  # is this bad? looks like the object is order on github side... so top should always been latest
    version = latest["name"]
    return version


def get_latest_install_command(version_name: str) -> str:
    """Generates a command to install the newest app version.

    Args:
        version_name (str): The name of the latest tag, e.g. v1.2.3

    Returns:
        str: The command to install the newest version.
    """
    repo_url = "https://github.com/British-Oceanographic-Data-Centre/APDS-Pusher"
    install_latest_url = f"{repo_url}@{version_name}"
    install_command = f"pip install git+{install_latest_url}"
    return install_command


def get_current_version() -> str:
    """Gets the currently installed version of the app.

    Returns:
        str: Version number, in the format v1.2.3
    """
    version_number = importlib_version("apds_pusher")
    return version_number if version_number[0] == "v" else f"v{version_number}"
