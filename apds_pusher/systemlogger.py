"""System logger."""
import logging
from pathlib import Path


class SystemLogger:
    """A class used to log messages to console and file."""

    def __init__(self, deployment_id: str, log_file_location: Path, deployment_location: Path) -> None:
        """Sets up the SystemLogger."""
        self.logger = logging.Logger("APDS")
        self.set_systemlog_filename(deployment_id, log_file_location, deployment_location)
        self.configure_console_logger()
        self.configure_file_logger()

    def set_systemlog_filename(self, deployment_id: str, log_file_location: Path, deployment_location: Path) -> None:
        """Creates the logfile name.

        It will attempt to create the filename by looking in 3 locations, stopping when successful
        - The location specified in the config file (log_file_location)
        - The location of the deployment
        - The current working directory.

        Once the logfile has been created, it will then set the 'self.log_file_name'
        attribute, which is used the configure_file_logger method.
        """
        # A list of locations to try to create the logfile
        locations = [log_file_location, deployment_location, Path.cwd()]

        # Getting the first valid path from the available choices
        valid = [loc for loc in locations if loc.is_dir()][0]

        # using the chosen path to return the logfile name
        log_file_name = valid / (deployment_id + ".log")

        # Log the filepath to the console as a reference
        self.logger.info("Log file located at: %s", log_file_name)

        # Then set the log_file_name attribute to the newly created path
        self.log_file_name = log_file_name

    def configure_file_logger(self) -> None:
        """Sets up logging to file."""
        file_out = logging.FileHandler(self.log_file_name)
        file_out.setLevel(logging.DEBUG)
        file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_out.setFormatter(file_format)
        self.logger.addHandler(file_out)

    def configure_console_logger(self) -> None:
        """Sets up logging to the console."""
        console_out = logging.StreamHandler()
        console_out.setLevel(logging.DEBUG)
        console_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        console_out.setFormatter(console_format)
        self.logger.addHandler(console_out)

    def info(self, msg: str) -> None:
        """Adds an information line to the console and file."""
        self.logger.info(msg)

    def warn(self, msg: str) -> None:
        """Adds a warning line to the console and file."""
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        """Adds an error line to the console and file."""
        self.logger.error(msg)

    def critical(self, msg: str) -> None:
        """Adds a critcal line to the console and file."""
        self.logger.critical(msg)

    def debug(self, msg: str) -> None:
        """Adds a debug line to the console and file."""
        self.logger.debug(msg)
