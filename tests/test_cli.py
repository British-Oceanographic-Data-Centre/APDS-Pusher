"""Test CLI."""
from pathlib import Path

import click
import pytest

from apds_pusher import config_parser, main


@pytest.fixture(name="config_path")
def config_path_fixture():
    """A fixture containing a path to a valid configuration JSON file."""
    return Path(__file__).parent / "example_config.json"


def test_load_configuration_file(config_path):
    """Check that the correct data is returned from a call to load the config file."""
    config = main.load_configuration_file(config_path)

    assert isinstance(config, config_parser.Configuration)


@pytest.mark.parametrize(
    "exception_type",
    [
        config_parser.ExtraFieldError,
        config_parser.MissingFieldError,
        config_parser.BlankValueError,
    ],
)
def test_click_exception_on_parse_error(mocker, config_path, exception_type):
    """Check that the correct exception is raised when a parsing error occurs."""
    mocker.patch.object(config_parser.Configuration, "from_dict_validated", side_effect=exception_type("an exception"))

    with pytest.raises(click.ClickException):
        main.load_configuration_file(config_path)
