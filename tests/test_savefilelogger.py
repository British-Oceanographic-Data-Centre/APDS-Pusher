"""Tests for the savefile logger."""

import sys
from pathlib import Path

from apds_pusher import savefilelogger


def test_logfile_in_logfile_folder(tmp_path):
    """Tests that an instance of the logger is created in the correct location.

    This test passes if the file is successfully created and can be
    found in the location as specified by the user.
    """
    # Create temporary folder for logfile to live
    temporary_directory = tmp_path / "logs"
    temporary_directory.mkdir()

    temporary_glider_directory = tmp_path / "gliders"
    temporary_glider_directory.mkdir()

    # Create test instance of savefileLogger
    instance = savefilelogger.FileLogger(temporary_directory, temporary_glider_directory, "1234")
    instance.write_to_log_file("test")

    # Assert file has been created in the correct place (log folder)
    assert Path(temporary_directory, "deployment-1234-log.out").is_file()


def test_logfile_in_glider_folder(tmp_path):
    """Tests that an instance of the logger is created in the glider directory.

    If the first directory is inaccessible, then the code should resort to saving
    the logger in the glider folder directory, which is specified by the user.

    This test passes if the file can be found in the glider folder.
    """
    # Used to pass reference to a folder, without creating it
    temporary_directory = tmp_path / "logs"

    temporary_glider_folder = tmp_path / "gliders"
    temporary_glider_folder.mkdir()

    # Test instance of savefileLogger with a bad directory as 1st argument
    instance = savefilelogger.FileLogger(temporary_directory, temporary_glider_folder, "1234")
    instance.write_to_log_file("test")

    # Assert file has been created
    assert Path(temporary_glider_folder, "deployment-1234-log.out").is_file()


def test_filewrite(tmp_path):
    """When a deployment is completed, its filename is written to the log file.

    This test passes if the filename can be found within the file, once the
    'write_to_log_file' method has been called.
    """
    temporary_log_folder = tmp_path / "logs"
    temporary_log_folder.mkdir()

    temporary_glider_folder = tmp_path / "gliders"
    temporary_glider_folder.mkdir()

    # Create test instance of savefileLogger
    instance = savefilelogger.FileLogger(temporary_log_folder, temporary_glider_folder, "1234")
    filename = "a-test-file.cac"
    instance.write_to_log_file(filename)

    # Assert file has been created
    path_to_file = Path(temporary_log_folder, "deployment-1234-log.out")
    file_contents = path_to_file.read_text(encoding=sys.getdefaultencoding())
    assert filename in file_contents
