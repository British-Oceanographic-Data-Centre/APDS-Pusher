"""Device flow authentication .A user code and tiny url is provided."""


from typing import Dict, Tuple

import requests

from apds_pusher.config_parser import Configuration


def get_device_code(client_id: str, auth_domain: str) -> Dict:
    """Method to authorize the device.

    The verification url and the user code is returned for user to authorise his/her device. User has to
    confirm their device by comparing at the device code.

    Args:
       auth_domain (str) : The url of the auth domain
       client_id (str) : client id of the APDS pusher application

    Returns :
        the response payload containing the user code and tinyurl
    """
    payload = {
        "scope": "openid email",
        "audience": "apds.livbodcdatadev.bodc.me",
        "client_id": client_id,
    }
    headers = {"content-type": "application/json"}
    res = requests.post("https://" + auth_domain + "/oauth/device/code", headers=headers, json=payload)
    return res.json()


def authenticate(config: Configuration) -> Tuple[str, str, int]:
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

    # retrieves the URL and challenge code for device flow
    device_data = get_device_code(client_id, auth_domain)

    user_code = device_data["user_code"]
    url = device_data["verification_uri"]
    expires_in = device_data["expires_in"]

    return (url, user_code, expires_in)
