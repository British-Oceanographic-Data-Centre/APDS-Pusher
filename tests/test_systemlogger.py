"""Tests for the system logger."""
import sys
from pathlib import Path

import pytest

from apds_pusher import systemlogger


def test_systemlogfile_in_logfile_folder(tmp_path):
    """Tests that the system logger is created and saved in the correct location.

    This test passes if the file is successfully created in the log folder,
    and is not created in the glider folder.
    """
    # Create temporary folders for logs and glider files
    temporary_log_directory = tmp_path / "logs/"
    temporary_log_directory.mkdir()

    temporary_glider_directory = tmp_path / "gliders/"
    temporary_glider_directory.mkdir()

    # Create test instance of the system logger
    instance = systemlogger.SystemLogger("1234", temporary_log_directory, temporary_glider_directory)
    assert isinstance(instance, systemlogger.SystemLogger)

    # Assert file has been created in the correct place (log folder)
    assert Path(temporary_log_directory, "1234.log").is_file()

    # Assert file has not been added to the glider folder
    assert not Path(temporary_glider_directory, "1234.log").is_file()


def test_systemlogfile_in_glider_folder(tmp_path):
    """Tests that system logger is created in alternate location

    If the logfile argument points to an invalid directory, the program
    will attempt to save the log file in the glider folder. This test passes an invalid
    directory and then checks to see if the logs are saved in the glider folder.
    """
    # Create temporary folders for logs and glider files
    temporary_log_directory = tmp_path / "logs"
    temporary_log_directory.mkdir()

    temporary_glider_directory = tmp_path / "gliders"
    temporary_glider_directory.mkdir()

    # Create test instance of the system logger
    systemlogger.SystemLogger("1234", Path("incorrect_dir"), temporary_glider_directory)

    # Assert file has not been created in the log folder
    assert not Path(temporary_log_directory, "1234.log").is_file()

    # Assert file has been correctly added to the glider folder
    assert Path(temporary_glider_directory, "1234.log").is_file()


@pytest.fixture(name="logging_instance")
def system_logger_fixture(tmp_path):
    """A fixture containing an instance of the system logger."""
    temporary_log_directory = tmp_path / "logs"
    temporary_log_directory.mkdir()

    temporary_deploy_directory = tmp_path / "gliders"
    temporary_deploy_directory.mkdir()
    return systemlogger.SystemLogger("1234", temporary_log_directory, temporary_deploy_directory)


def test_check_logging_info(tmp_path, capfd, logging_instance):
    """Checks logfile and std. out to verify if info message was successful."""
    logging_instance.info("info message from test")

    # Capture std. out
    _, captured_stdout = capfd.readouterr()

    # Check that the info mesage appears in the file, and in the console
    path_to_file = Path(tmp_path / "logs" / "1234.log")
    file_contents = path_to_file.read_text(encoding=sys.getdefaultencoding())
    assert "info message from test" in file_contents
    assert "info message from test" in captured_stdout


def test_check_logging_debug(tmp_path, capfd, logging_instance):
    """Checks logfile and std. out to verify if debug message was successful."""
    logging_instance.debug("debug message from test")

    # Capture std. out
    _, captured_stdout = capfd.readouterr()

    # Check that the info mesage appears in the file, and in the console
    path_to_file = Path(tmp_path / "logs", "1234.log")
    file_contents = path_to_file.read_text(encoding=sys.getdefaultencoding())
    assert "debug message from test" in file_contents
    assert "debug message from test" in captured_stdout


def test_check_logging_warn(tmp_path, capfd, logging_instance):
    """Checks logfile and std. out to verify if warn message was successful."""
    logging_instance.warn("warning message from test")

    # Capture std. out
    _, captured_stdout = capfd.readouterr()

    # Check that the info mesage appears in the file, and in the console
    path_to_file = Path(tmp_path / "logs", "1234.log")
    file_contents = path_to_file.read_text(encoding=sys.getdefaultencoding())
    assert "warning message from test" in file_contents
    assert "warning message from test" in captured_stdout


def test_check_logging_error(tmp_path, capfd, logging_instance):
    """Checks logfile and std. out to verify if error message was successful."""
    logging_instance.error("error message from test")

    # Capture std. out
    _, captured_stdout = capfd.readouterr()

    # Check that the info mesage appears in the file, and in the console
    path_to_file = Path(tmp_path / "logs", "1234.log")
    file_contents = path_to_file.read_text(encoding=sys.getdefaultencoding())
    assert "error message from test" in file_contents
    assert "error message from test" in captured_stdout


def test_check_logging_critical(tmp_path, capfd, logging_instance):
    """Checks logfile and std. out to verify if critical message was successful."""
    logging_instance.critical("critical message from test")

    # Capture std. out
    _, captured_stdout = capfd.readouterr()

    # Check that the info mesage appears in the file, and in the console
    path_to_file = Path(tmp_path / "logs", "1234.log")
    file_contents = path_to_file.read_text(encoding=sys.getdefaultencoding())
    assert "critical message from test" in file_contents
    assert "critical message from test" in captured_stdout
