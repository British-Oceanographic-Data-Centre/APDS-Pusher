"""Test default authentication. """

import pytest
import responses

from apds_pusher import config_parser, device_auth

JSON_RESPONSE = {
    "device_code": "Ag_EE...ko1p",
    "user_code": "TEST_CODE",
    "verification_uri": "https://test.org",
    "verification_uri_complete": "https://test.org/activate?user_code=TEST_CODE",
    "expires_in": 900,
    "interval": 5,
}


@pytest.fixture(name="pusher_config")
def fixture_pusher_config():
    """Creating instance of config class"""
    return config_parser.Configuration(
        client_id="an_id",
        auth0_tenant="a_tenant.com",
        bodc_archive_url="url",
        file_formats=[".dat"],
        archive_checker_frequency=1000,
        save_file_location="a_path_to_file",
        log_file_location="a_path_to_file",
    )


@responses.activate
def test_get_device_code(pusher_config):
    """Check the responses for device flow is working"""
    mockresp = responses.Response(
        method="POST",
        url="https://a_tenant.com/oauth/device/code",
        json=JSON_RESPONSE,
        status=200,
    )
    responses.add(mockresp)
    fake_config = pusher_config
    resp = device_auth.get_device_code(fake_config.client_id, fake_config.auth0_tenant)

    assert resp == {
        "device_code": "Ag_EE...ko1p",
        "user_code": "TEST_CODE",
        "verification_uri": "https://test.org",
        "verification_uri_complete": "https://test.org/activate?user_code=TEST_CODE",
        "expires_in": 900,
        "interval": 5,
    }

    assert len(responses.calls) == 1


def test_authenticate(mocker, pusher_config):
    """Checking if the values are returned by auth function."""
    mocker.patch.object(device_auth, "get_device_code", return_value=JSON_RESPONSE)

    auth_dtls = device_auth.authenticate(pusher_config)

    assert auth_dtls == ("https://test.org", "TEST_CODE", 900)
