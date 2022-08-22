"""Test default authentication. """


from queue import Queue

import polling2  # type: ignore
import pytest
import requests
import responses

from apds_pusher import config_parser, device_auth

JSON_RESPONSE = {
    "device_code": "Ag_EE...ko1p",
    "user_code": "TEST_CODE",
    "verification_uri": "https://test.org",
    "verification_uri_complete": "https://test.org/activate?user_code=TEST_CODE",
    "expires_in": 0.1,
    "interval": 5,
}

DEVICE_CODE_RESPONSE = {
    "device_code": "TESTDEVICECODE",
    "user_code": "TEST_USER_CODE",
    "verification_uri": "https://test.org",
    "verification_uri_complete": "https://test.org/activate?user_code=TEST_USER_CODE",
    "expires_in": 0.1,
    "interval": 5,
}

SAMPLE_ACCESS_TOKEN = {
    "access_token": "Testtoken",
    "id_token": "Test_id_token",
    "scope": "openid email",
    "expires_in": "86400",
    "token_type": "Bearer",
}
SAMPLE_EXCEPTION = "expired device code"


@pytest.fixture(name="mock_response_403")
def mock_error_response_code(mocker):
    """Creating a mock error response"""
    resp_body = Queue()  # instantiate the queue.Queue
    item = {"error": "error", "error_description": "unknown device code"}
    resp_body.put(item)

    error_response_mock = mocker.Mock()
    type(error_response_mock).values = Queue
    error_response_mock.values = mocker.PropertyMock(return_value=resp_body)
    return error_response_mock


@pytest.fixture(name="mock_response_200")
def mock_ok_response_code(mocker):
    """Creating a mock response"""
    ok_response_mock = mocker.Mock()
    type(ok_response_mock).status_code = mocker.PropertyMock(return_value=200)
    return ok_response_mock


@pytest.fixture(name="pusher_config")
def fixture_pusher_config():
    """Creating instance of config class"""
    return config_parser.Configuration(
        client_id="an_id",
        client_secret="A secret",
        auth2_audience= "an audience",
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

    resp = device_auth.get_device_code(pusher_config.client_id, pusher_config.auth2_audience, pusher_config.auth0_tenant)

    assert resp == {
        "device_code": "Ag_EE...ko1p",
        "user_code": "TEST_CODE",
        "verification_uri": "https://test.org",
        "verification_uri_complete": "https://test.org/activate?user_code=TEST_CODE",
        "expires_in": 0.1,
        "interval": 5,
    }

    assert len(responses.calls) == 1


@responses.activate
def test_get_device_code_with_error(pusher_config):
    """Check the errors for  when device flow is working"""
    mockresp = responses.Response(
        method="POST",
        url="https://a_tenant.com/oauth/device/code",
        json={"error": "invalid", "error_description": "Test Error."},
        status=200,
    )
    responses.add(mockresp)

    with pytest.raises(device_auth.DeviceCodeError) as unknerr:
        device_auth.get_device_code(pusher_config.client_id, pusher_config.auth2_audience, pusher_config.auth0_tenant)

    assert unknerr.value.args[0] == "Device code not generated. \nError: Test Error."


@pytest.mark.parametrize(
    "resp_body,expected",
    [
        (requests.exceptions.HTTPError(), "HTTP error while generating Device Code"),
        (requests.exceptions.ConnectionError(), "Connection error while generating Device Code"),
        (requests.exceptions.Timeout(), "Timeout error while generating Device Code"),
        (requests.exceptions.RequestException(), "Unknown error while generating Device Code"),
    ],
)
@responses.activate
def test_get_device_code_with_exception_2(resp_body, expected, pusher_config):
    """Check the exceptions for device flow"""
    mockresp = responses.Response(
        method="POST",
        url="https://a_tenant.com/oauth/device/code",
        status=404,
        body=resp_body,
    )
    responses.add(mockresp)

    with pytest.raises(device_auth.DeviceCodeError) as err:
        device_auth.get_device_code(pusher_config.client_id, pusher_config.auth2_audience, pusher_config.auth0_tenant)

    assert err.value.args[0] == expected


def test_authenticate(mocker, pusher_config):
    """Checking if the values are returned by auth function."""
    mocker.patch.object(device_auth, "get_device_code", return_value=JSON_RESPONSE)

    auth_dtls = device_auth.authenticate(pusher_config)

    assert auth_dtls == ("https://test.org", "TEST_CODE", 0.1, "Ag_EE...ko1p", 5)


def test_is_correct_response(mock_response_200):
    """Checking if the values are returned by check response function."""
    resp_dtls = device_auth.is_correct_response(mock_response_200)

    assert resp_dtls is True


def test_raise_if_err_contains_expired():
    """Check if exceptions with expired device code is picked"""
    with pytest.raises(device_auth.DeviceCodeError) as timeouterr:
        device_auth.raise_if_err_contains_expired(SAMPLE_EXCEPTION)

    assert timeouterr.value.args[0] == "Device code is expired. Start APDS Pusher again to obtain new code"


@responses.activate
def test_receive_access_token_from_device_code(pusher_config):
    """Checking if the accesstoken are generated from valid device code."""
    mockresp = responses.Response(
        method="POST",
        url="https://a_tenant.com/oauth/token",
        json=SAMPLE_ACCESS_TOKEN,
        status=200,
    )
    responses.add(mockresp)

    access_token = device_auth.receive_access_token_from_device_code(DEVICE_CODE_RESPONSE, pusher_config)

    assert access_token["access_token"] == "Testtoken"


@responses.activate
def test_receive_access_token_from_device_code_exception(mock_response_403, mocker, pusher_config):
    """Checking if exception for a unknown reason is captured."""

    mocker.patch.object(
        polling2,
        "poll",
        side_effect=polling2.TimeoutException(values=mock_response_403.values),
    )

    with pytest.raises(device_auth.DeviceCodeError) as unknownerr:
        device_auth.receive_access_token_from_device_code(JSON_RESPONSE, pusher_config)

    assert unknownerr.value.args[0] == "Unknown error while generating device code"
