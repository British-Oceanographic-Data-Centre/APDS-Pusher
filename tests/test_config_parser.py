"""Test configuration parser."""
from dataclasses import asdict

import pytest

from apds_pusher import config_parser


@pytest.fixture(name="config_dict")
def config_dict_fixture():
    """A fixture containing a valid configuration dictionary."""
    return dict(
        client_id="an_id",
        auth0_tenant="a_tenant",
        bodc_archive_url="url",
        file_formats=[".dat"],
        archive_checker_frequency=1000,
    )


def test_dataclass_creation(config_dict):
    """Check that the dataclass is correctly populated when instantiated using the class method."""
    config = config_parser.Configuration.from_dict_validated(config_dict)

    assert config_dict == asdict(config)


def test_additional_value_error(config_dict):
    """Check that the right exception is raised when additional values are present."""
    config_dict["non_existant_key"] = "some data"

    with pytest.raises(config_parser.ExtraFieldError):
        config_parser.Configuration.from_dict_validated(config_dict)


def test_missing_value_error(config_dict):
    """Check that the right exception is raised when there is a missing field."""
    del config_dict["client_id"]

    with pytest.raises(config_parser.MissingFieldError):
        config_parser.Configuration.from_dict_validated(config_dict)


def test_blank_value_error(config_dict):
    """Check that the right exception is raised when there is a blank value."""
    config_dict["file_formats"] = []

    with pytest.raises(config_parser.BlankValueError):
        config_parser.Configuration.from_dict_validated(config_dict)
