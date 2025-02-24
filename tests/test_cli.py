"""Test CLI."""

from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from apds_pusher import __main__, config_parser
from apds_pusher.__main__ import recovery


@pytest.fixture(name="config_path")
def config_path_fixture():
    """A fixture containing a path to a valid configuration JSON file."""
    return Path(__file__).parent / "example_config.json"


def test_load_configuration_file(config_path):
    """Check that the correct data is returned from a call to load the config file."""
    config = __main__.load_configuration_file(config_path)

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
        __main__.load_configuration_file(config_path)


def test_recovery_command(config_path, mocker, tmp_path):
    # Mock the load_configuration_file function
    config = __main__.load_configuration_file(config_path)
    mock_pusher_group = mocker.patch('apds_pusher.__main__.pusher_group')
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    
    runner = CliRunner()
    result = runner.invoke(
        recovery,
        [
            "--deployment-id", "test-deployment",
            "--data-directory", str(data_directory),
            "--config-file", str(config_path),
            "--production",
            "--dry-run",
            "--recursive",
            "--trace",
        ]
    )
    
    assert result.exit_code == 0, result.output
    assert "Files is going to be pulled for the recovered deployment" in result.output

def test_recovery_missing_args():
    """Test the recovery command with missing required arguments."""
    runner = CliRunner()
    result = runner.invoke(recovery, [])
    
    assert result.exit_code != 0
    assert "Usage: recovery" in result.output  # More flexible assertion
