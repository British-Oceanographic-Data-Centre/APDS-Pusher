"""File to hold logic for refreshing an oauth2 access token."""

import requests

from apds_pusher.config_parser import Configuration


class AccessCodeError(Exception):
    """Exception raised when errors in the refreshed access token."""


def get_access_token_from_refresh_token(refresh_token: str, config: Configuration) -> str:
    """Retrieve the access tokens for expired tokens using refresh tokens.

    The access tokens are returned for expired access tokens
    Args:
       refresh_token dict : details of the access token for which a refresh token is required
       config :A configuration class object

    Returns :
        the access token
    """
    auth_domain = config.auth0_tenant
    client_id = config.client_id
    client_secret = config.client_secret

    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    headers = {"content-type": "application/json"}
    try:
        res = requests.post("https://" + auth_domain + "/oauth/token", headers=headers, json=payload)
        res.raise_for_status()

    except requests.exceptions.HTTPError as errhttp:
        raise AccessCodeError("Http Error while refreshing token") from errhttp
    except requests.exceptions.ConnectionError as errconn:
        raise AccessCodeError("Connection Error while refreshing token") from errconn
    except requests.exceptions.Timeout as errtimeout:
        raise AccessCodeError("Timeout eror while refreshing token") from errtimeout
    except requests.exceptions.RequestException as errreq:
        raise AccessCodeError("Unknown error while refreshing token") from errreq

    if "error" in res.json():
        raise AccessCodeError(f"Refresh token not generated. \nError: {res.json()['error_description']}")
    access_token_details = res.json()
    return access_token_details["access_token"]
