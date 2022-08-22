"""Tests for code which interacts with the API."""
import pytest
import responses

from apds_pusher.send_to_archive import HoldingsAccessError, call_holdings_endpoint, return_existing_glider_files

valid_holdings_json = {
    "files": {
        ".cac_Count": 2,
        ".cac_files": [
            {"name": "4fca660c.cac", "checksum": "d3e70ff5f82bb20254a6fc7bfca1bc7f", "date": "2019-02-21T08:03:55"},
            {"name": "ad21ffc1.cac", "checksum": "88765af77894a8e802adeb7cf4eef910", "date": "2019-02-21T08:04:03"},
        ],
    }
}


@pytest.fixture(name="valid_holdings_call")
def fixture_valid_api_call():
    """A mock API call to the holdings endpoint."""
    mock_response = responses.Response(
        method="GET",
        url="https://submit-data.bodc.ac.uk/apds-archive-beta/holdings/441",
        json=valid_holdings_json,
        status=200,
    )
    return mock_response


@responses.activate
def test_holdings_endpoint_for_json(valid_holdings_call):
    """Check the holdings endpoint returns a JSON object, given a valid deployment ID."""
    responses.add(valid_holdings_call)
    holdings_response = call_holdings_endpoint("https://submit-data.bodc.ac.uk/apds-archive-beta/", "441")
    assert isinstance(holdings_response, dict)
    assert len(responses.calls) == 1


@responses.activate
def test_exception_is_raised_with_invalid_call():
    """Check correct exception is raised when calling API with invalid URL."""
    mock_response = responses.Response(
        method="GET",
        url="https://api.linked-systems.uk/api/meta/v2/holdings/",
        status=404,
    )
    responses.add(mock_response)

    with pytest.raises(HoldingsAccessError):
        call_holdings_endpoint("https://submit.uk/apds-archive-beta/", "")


@responses.activate
def test_set_is_constructed_from_json(valid_holdings_call):
    """Check that a set can be constructed, given a valid API call."""
    responses.add(valid_holdings_call)
    response = return_existing_glider_files("https://submit-data.bodc.ac.uk/apds-archive-beta/", "441")

    assert len(response) == 2
    assert response == {"ad21ffc1.cac", "4fca660c.cac"}
    assert isinstance(response, set)
