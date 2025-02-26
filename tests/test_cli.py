"""Test CLI."""

from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from apds_pusher import __main__, config_parser
from apds_pusher.__main__ import recovery
from apds_pusher.utils.deployment_utils import (
    load_configuration_file,
)


@pytest.fixture(name="config_path_fixture")
def config_path_fixture():
    """A fixture containing a path to a valid configuration JSON file."""
    print("FIXTURE")
    print(Path(__file__).parent / "example_config.json")
    return Path(__file__).parent / "example_config.json"


@pytest.fixture(name="config_path_recovery")
def config_path_recovery():
    """A fixture containing a path to a valid configuration JSON file."""
    return Path(__file__).parent / "recovery_config.json"


def test_load_configuration_file(config_path_fixture):
    """Check that the correct data is returned from a call to load the config file."""
    config = load_configuration_file(config_path_fixture)
    print(f"Loaded Config: {config}")  # Debugging print

    assert isinstance(config, config_parser.Configuration)


@pytest.mark.parametrize(
    "exception_type",
    [
        config_parser.ExtraFieldError,
        config_parser.MissingFieldError,
        config_parser.BlankValueError,
    ],
)
def test_click_exception_on_parse_error(mocker, config_path_fixture, exception_type):
    """Check that the correct exception is raised when a parsing error occurs."""
    mocker.patch.object(config_parser.Configuration, "from_dict_validated", side_effect=exception_type("an exception"))

    with pytest.raises(click.ClickException):
        load_configuration_file(config_path_fixture)


def test_recovery_command(config_path_recovery, tmp_path, mocker):
    """Checking the Recovery command"""
    # Mock the load_configuration_file function
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    mock_process = mocker.patch("apds_pusher.__main__.process_deployment")

    runner = CliRunner()
    result = runner.invoke(
        recovery,
        [
            "--deployment-id",
            "test-deployment",
            "--data-directory",
            str(data_directory),
            "--config-file",
            str(config_path_recovery),
            "--production",
            "--dry-run",
            "--non-recursive",
            "--trace",
        ],
    )

    assert result.exit_code == 0, result.output
    mock_process.assert_called_once_with(
        "test-deployment", data_directory, config_path_recovery, True, True, False, True, "Recovery"
    )


def test_recovery_missing_args():
    """Test the recovery command with missing required arguments."""
    runner = CliRunner()
    result = runner.invoke(recovery, [])

    assert result.exit_code != 0, result
    assert "Usage: recovery" in result.output  # More flexible assertion
