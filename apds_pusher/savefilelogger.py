"""Logging class used keep track files of sent files."""

import sys
from datetime import datetime as dt
from pathlib import Path


class FileLogger:
    """Class to handle the logging of files that have been sent to Archive."""

    def __init__(self, save_file_location: Path, deployment_location: Path, deployment_id: str) -> None:
        """Perform setup for FileLogger."""
        self.set_filelog_filename(save_file_location, deployment_location, deployment_id)
        self.write_initial_line_to_file()

    def set_filelog_filename(self, save_file_location: Path, deployment_location: Path, deployment_id: str) -> None:
        """Determine and set the save location of the savefile.

        It will attempt to create the file in 3 locations, stopping when successful
        - The location specified in the config file (save_file_location)
        - The location of the deployment
        - The current working directory.

        Once successful it will then set the attribute (self.file_path)
        Which is used by by the self.write_to_log_file method.

        """
        # A list of locations to try to create the savefile
        locations = [save_file_location, deployment_location, Path.cwd()]

        # Getting the first valid path from the available choices
        valid = [loc for loc in locations if loc.is_dir()][0]

        # using the chosen path to return the savefile name
        log_file_name = valid / f"deployment-{deployment_id}-log.out"

        # Set the attribute to file path, to allow for file writing later on
        self.file_path = log_file_name

    def write_initial_line_to_file(self) -> None:
        """Write a summary line to the top of the save file."""
        with open(self.file_path, "w", encoding=sys.getdefaultencoding()) as file:
            file.write("This file will contain a record of all files sent to the BODC archive.\n")

    def write_to_log_file(self, filename: str) -> None:
        """Write filename and current date/time to file.

        Args:
            filename: The full path to the file that has been submitted.
        """
        time_string = dt.now().strftime("%d-%m-%Y %H:%M:%S")
        string_to_write = f"File: {filename} Uploaded at: {time_string}\n"
        with open(self.file_path, "a", encoding=sys.getdefaultencoding()) as file:
            file.write(string_to_write)
