"""Test token refresher. """


import pytest
import requests
import responses

from apds_pusher import config_parser, token_refresher

JSON_RESPONSE = {
    "access_token": "New_access_token",
    "refresh_token": "Test_refresh_token",
    "id_token": "New_id_token",
    "token_type": "Bearer",
    "expires_in": 86400,
}


@pytest.fixture(name="refresh_token")
def fixture_access_token():
    """Creating instance of expired token"""
    return JSON_RESPONSE["refresh_token"]


@pytest.fixture(name="pusher_config")
def fixture_pusher_config():
    """Creating instance of config class"""
    return config_parser.Configuration(
        client_id="a_clientid",
        client_secret="A secret",
        auth2_audience= "an audience",
        auth0_tenant="a_tenant.com",
        bodc_archive_url="url",
        file_formats=[".dat"],
        archive_checker_frequency=100,
        save_file_location="a_path",
        log_file_location="a_path",
    )


@responses.activate
def test_get_access_token_from_refresh_token(refresh_token, pusher_config):
    """Check the responses for refresh token flow is working"""
    mockresp = responses.Response(
        method="POST",
        url="https://a_tenant.com/oauth/token",
        json=JSON_RESPONSE,
        status=200,
    )
    responses.add(mockresp)

    resp = token_refresher.get_access_token_from_refresh_token(refresh_token, pusher_config)

    assert resp == "New_access_token"
    assert len(responses.calls) == 1


@responses.activate
def test_get_access_token_from_refresh_token_error(refresh_token, pusher_config):
    """Check the responses for refresher token when error"""
    mockresp = responses.Response(
        method="POST",
        url="https://a_tenant.com/oauth/token",
        json={"error": "error", "error_description": "Some test error"},
        status=200,
    )
    responses.add(mockresp)

    with pytest.raises(token_refresher.AccessCodeError) as err:
        token_refresher.get_access_token_from_refresh_token(refresh_token, pusher_config)

    assert err.value.args[0] == "Refresh token not generated. \nError: Some test error"


@pytest.mark.parametrize(
    "resp_body,expected",
    [
        (requests.exceptions.HTTPError(), "Http Error while refreshing token"),
        (requests.exceptions.ConnectionError(), "Connection Error while refreshing token"),
        (requests.exceptions.Timeout(), "Timeout eror while refreshing token"),
        (requests.exceptions.RequestException(), "Unknown error while refreshing token"),
    ],
)
@responses.activate
def test_get_access_token_from_refresh_token_exception(resp_body, expected, refresh_token, pusher_config):
    """Check the exceptions when a refresher token is requested."""
    mockresp = responses.Response(
        method="POST",
        url="https://a_tenant.com/oauth/token",
        status=404,
        body=resp_body,
    )
    responses.add(mockresp)
    with pytest.raises(token_refresher.AccessCodeError) as err:
        token_refresher.get_access_token_from_refresh_token(refresh_token, pusher_config)

    assert err.value.args[0] == expected
