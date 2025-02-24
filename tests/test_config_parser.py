"""Test configuration parser."""

from dataclasses import asdict
from pathlib import Path

import pytest

from apds_pusher import config_parser


@pytest.fixture(name="config_dict")
def config_dict_fixture():
    """A fixture containing a valid configuration dictionary."""
    return {
        "client_id": "an_id",
        "auth0_tenant": "a_tenant",
        "auth2_audience": "an audience",
        "client_secret": "a secret",
        "bodc_archive_url": "url",
        "file_formats": [".dat"],
        "archive_checker_frequency": 1000,
        "save_file_location": "a_path",
        "log_file_location": "a_path",
    }


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


def test_pathfields_are_converted_to_paths(config_dict):
    """Check that the save/log locations are correctly returned as Paths."""
    config_dict = config_parser.Configuration.from_dict_validated(config_dict)
    assert isinstance(config_dict.save_file_location, Path)
    assert isinstance(config_dict.log_file_location, Path)


@pytest.mark.parametrize("bad_path", [1, {"a": "b"}, ("a", "b"), 1.2])
@pytest.mark.parametrize("path_field", ["save_file_location", "log_file_location"])
def test_bad_pathfields_raise_exception(config_dict, path_field, bad_path):
    """Check that bad values for save/log locations raise the correct exception."""
    config_dict[path_field] = bad_path

    with pytest.raises(config_parser.InvalidPathError) as exc:
        config_dict = config_parser.Configuration.from_dict_validated(config_dict)

    assert exc.value.args[0] == f"{path_field} is an invalid path."
