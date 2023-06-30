"""System logger."""
import logging
from pathlib import Path


class SystemLogger(logging.getLoggerClass()):  # type: ignore
    """A class used to log messages to console and file."""

    def __init__(
        self, deployment_id: str, log_file_location: Path, deployment_location: Path, trace: bool = False
    ) -> None:
        """Set up the SystemLogger."""
        super().__init__("APDS")
        self.set_systemlog_filename(deployment_id, log_file_location, deployment_location)
        self.configure_console_logger(trace=trace)
        self.configure_file_logger(trace=trace)

    def set_systemlog_filename(self, deployment_id: str, log_file_location: Path, deployment_location: Path) -> None:
        """Create the logfile name.

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
        self.info("Log file located at: %s", log_file_name)

        # Then set the log_file_name attribute to the newly created path
        self.log_file_name = log_file_name

    def configure_file_logger(self, trace: bool = False) -> None:
        """Set up logging to file."""
        file_out = logging.FileHandler(self.log_file_name)
        if trace:
            file_out.setLevel(logging.DEBUG)
        else:
            file_out.setLevel(logging.INFO)
        file_format = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s:%(funcName)s:%(lineno)d :- %(message)s")
        file_out.setFormatter(file_format)
        self.addHandler(file_out)

    def configure_console_logger(self, trace: bool = False) -> None:
        """Set up logging to the console."""
        console_out = logging.StreamHandler()

        if trace:
            console_out.setLevel(logging.DEBUG)
            console_format = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s:%(module)s:%(lineno)d :- %("
                "message)s"  # pylint: disable=implicit-str-concat
            )
        else:
            console_out.setLevel(logging.WARNING)
            console_format = logging.Formatter("%(levelname)s - %(name)s :- %(message)s")

        console_out.setFormatter(console_format)
        self.addHandler(console_out)
