"""Tests for the system logger."""
from pathlib import Path

from apds_pusher import filepusher


def test_retrieve_glider_file_paths(tmp_path):
    """Tests that all glider filepaths are retrieved"""
    # Temporary directory to store files
    temporary_directory = tmp_path / "logs/"
    temporary_directory.mkdir()

    # Iterate through and create files in temporary directory
    test_filenames = ["file1.cac", "file2.sbd", "file123.tbd", "abcde.cac"]
    for filename in test_filenames + ["spreadsheet.csv"]:
        glider_directory = tmp_path / "logs/" / filename
        glider_directory.touch()

    # Call function to attempt to retrieve .tbd, .cac and .sbd files only.
    retrieved_files = filepusher.retrieve_glider_file_paths(temporary_directory, [".tbd", ".cac", ".sbd"])

    # Check the CSV file was not included in the retrieved file paths
    assert Path(temporary_directory, "spreadsheet.csv") not in retrieved_files

    # Check that the required files match the ones that were actually retrieved
    assert set(retrieved_files) == {tmp_path / "logs/" / fname for fname in test_filenames}
