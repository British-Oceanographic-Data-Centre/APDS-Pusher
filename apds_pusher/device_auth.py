"""Device flow authentication .A user code and tiny url is provided."""

import re
from typing import Dict, Tuple

import polling2  # type: ignore
import requests

from apds_pusher.config_parser import Configuration


class DeviceCodeError(Exception):
    """Exception raised when errors in the refreshed access token."""


# pylint: disable=R0801
def get_device_code(client_id: str, auth2_audience: str, auth_domain: str) -> Dict:
    """Method to authorize the device.

    The verification url and the user code is returned for user to authorise his/her device. User has to
    confirm their device by comparing at the device code.

    Args:
       auth_domain (str) : The url of the auth domain
       client_id (str) : client id of the APDS pusher application
       auth2_audience (str) : setting in 0auth2 to link request to target application

    Returns :
        the response payload containing the user code and tinyurl else will raise an exception
    """
    payload = {
        "scope": "openid email offline_access",
        "audience": auth2_audience,
        "client_id": client_id,
    }
    headers = {"content-type": "application/json"}
    try:
        res = requests.post(
            "https://" + auth_domain + "/oauth/device/code",
            headers=headers,
            json=payload,
            timeout=600,
        )
        res.raise_for_status()

    except requests.exceptions.HTTPError as errhttp:
        raise DeviceCodeError("HTTP error while generating Device Code") from errhttp
    except requests.exceptions.ConnectionError as errconn:
        raise DeviceCodeError("Connection error while generating Device Code") from errconn
    except requests.exceptions.Timeout as errtimeout:
        raise DeviceCodeError("Timeout error while generating Device Code") from errtimeout
    except requests.exceptions.RequestException as errreq:
        raise DeviceCodeError("Unknown error while generating Device Code") from errreq

    if "error" in res.json():
        raise DeviceCodeError(f"Device code not generated. \nError: {res.json()['error_description']}")
    access_token_details = res.json()
    return access_token_details


def authenticate(config: Configuration) -> Tuple[str, str, int, str, int]:
    """Method to return read config and authenticate config.

    The config section is read and generates a usercode for the device and later obtain a accesstoken

    Args:
       config :A configuration class object
    Returns:
       A tuple of user code, tiny url and time before the code expires
    """
    # reads the auth0 details
    auth_domain = config.auth0_tenant
    client_id = config.client_id
    auth2_audience = config.auth2_audience

    # retrieves the URL and challenge code for device flow
    device_data = get_device_code(client_id, auth2_audience, auth_domain)

    user_code = device_data["user_code"]
    url = device_data["verification_uri"]
    expires_in = device_data["expires_in"]
    device_code = device_data["device_code"]
    interval = device_data["interval"]

    return url, user_code, expires_in, device_code, interval


def is_correct_response(response: requests.Response) -> bool:
    """Check that the response returned success."""
    return response.status_code == 200


def raise_if_err_contains_expired(err_description: str) -> None:
    """Checking if device code is expired and raising exception.

    Args:
      err_description: the error description of the exception
    """
    desc_expired_token = re.compile(r"\bexpired\b")
    matches = desc_expired_token.search(err_description)
    if matches is not None:
        match = matches.group()
        if match:
            raise DeviceCodeError("Device code is expired. Start APDS Pusher again to obtain new code")


def receive_access_token_from_device_code(device_code_response: Dict, config: Configuration) -> Dict:
    """Start polling to recieve the access token.

    Args:
       device_code_response: a dict of all the required key-value for device auth
       config :A configuration class object
    Returns:
       A dict containing the access code and related information
    """
    # reads the auth0 details
    auth_domain = config.auth0_tenant
    client_id = config.client_id

    url = "https://" + auth_domain + "/oauth/token"
    headers = {"content-type": "application/json"}
    payload = {
        "audience": "apds.livbodcdatadev.bodc.me",
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": client_id,
        "device_code": device_code_response["device_code"],
    }
    try:
        access_token = polling2.poll(
            lambda: requests.post(url, headers=headers, json=payload, timeout=600),
            check_success=is_correct_response,
            step=device_code_response["interval"],
            timeout=device_code_response["expires_in"],
        )

    except polling2.TimeoutException as te_error:
        while not te_error.values.empty():
            # check if device code has expired and raise the exception
            response = te_error.values.get().json()
            raise_if_err_contains_expired(response["error_description"])
        # Raise error for any other reason
        raise DeviceCodeError("Unknown error while generating device code") from te_error
    return access_token.json()
