"""Tests for the system logger."""
from pathlib import Path

import pytest

from apds_pusher.config_parser import Configuration
from apds_pusher.filepusher import FilePusher


@pytest.fixture(name="config")
def config_dict_fixture(tmp_path):
    """A fixture containing a valid configuration dictionary."""
    save_location = tmp_path / "save"
    save_location.mkdir()

    log_location = tmp_path / "logs"
    log_location.mkdir()

    return Configuration(
        client_id="an_id",
        auth0_tenant="a_tenant",
        auth2_audience= "an audience",
        client_secret="a secret",
        bodc_archive_url="url",
        file_formats=[".cac", ".sbd", ".tbd"],
        archive_checker_frequency=1000,
        save_file_location=Path(save_location),
        log_file_location=Path(log_location),
    )


def test_instance_creation(tmp_path, config):
    """Test an instance can be created from valid inputs."""
    glider_dir = tmp_path / "gliders/"
    glider_dir.mkdir()

    instance = FilePusher("123", glider_dir, config, True, True, True, "", "")
    assert isinstance(instance, FilePusher)


def test_retrieve_glider_file_paths(tmp_path, config):
    """Tests that all glider filepaths are retrieved"""
    glider_dir = tmp_path / "gliders/"
    glider_dir.mkdir()

    # Iterate through and create files in temporary directory
    test_filenames = ["file1.cac", "file2.sbd", "file123.tbd", "abcde.cac"]
    for filename in test_filenames + ["spreadsheet.csv"]:
        glider_directory = tmp_path / "gliders/" / filename
        glider_directory.touch()

    # Set up a test instance
    instance = FilePusher("123", glider_dir, config, True, True, True, "", "")

    # Call function to attempt to retrieve .tbd, .cac and .sbd files only.
    retrieved_files = instance.retrieve_file_paths()

    # Check the CSV file was not included in the retrieved file paths
    assert Path(glider_dir, "spreadsheet.csv") not in retrieved_files

    # Check that the required files match the ones that were actually retrieved
    assert set(retrieved_files) == {tmp_path / "gliders/" / fname for fname in test_filenames}
