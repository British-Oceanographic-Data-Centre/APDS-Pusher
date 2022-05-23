"""Program to orchestrate push of files to the Archive API."""
from pathlib import Path

from apds_pusher.config_parser import Configuration
from apds_pusher.savefilelogger import FileLogger
from apds_pusher.send_to_archive import (
    AuthenticationError,
    FileUploadError,
    HoldingsAccessError,
    return_existing_glider_files,
    send_to_archive_api,
)
from apds_pusher.systemlogger import SystemLogger
from apds_pusher.token_refresher import token_refresher_call


class FilePusher:  # pylint: disable=too-many-instance-attributes
    """Class for managing interaction with Archive API."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        deployment_id: str,
        deployment_location: Path,
        config: Configuration,
        non_production: bool,
        dry_run: bool,
        access_token: str,
        refresh_token: str,
    ):
        """Setup for File Pusher."""
        self.deployment_id = deployment_id
        self.deployment_location = deployment_location
        self.config = config
        self.non_production = non_production
        self.dry_run = dry_run
        self.access_token = access_token
        self.refresh_token = refresh_token

        # Begin the logging
        self.initialise_logging()

    def run(self) -> None:
        """Rrigger the sending of files, or a dry run."""
        if self.dry_run:
            self.dry_run_send()
        else:
            self.send_files_to_api()

    def initialise_logging(self) -> None:
        """Sets up the file and system logging."""
        self.system_logger = SystemLogger(self.deployment_id, self.config.log_file_location, self.deployment_location)
        self.file_logger = FileLogger(self.config.save_file_location, self.deployment_location, self.deployment_id)
        self.system_logger.info(f"Save file located at: {self.file_logger.file_path}")

    def retrieve_file_paths(self) -> list:
        """Retrieve a list of absolute paths for desired glider files."""
        file_paths = []

        for file_format in self.config.file_formats:
            for path in Path(self.deployment_location).rglob(f"*{file_format}"):
                file_paths.append(path)

        return file_paths

    def dry_run_send(self) -> None:
        """Perform a dry run send of the files."""
        files_currently_in_archive = self.get_existing_glider_files_for_deployment()
        duplicates, files_added = 0, 0
        self.system_logger.info(f"Starting a dry run for deployment id: {self.deployment_id}")
        self.system_logger.info(f"There are currently {len(files_currently_in_archive)} files in the archive.")

        for file in self.retrieve_file_paths():
            if file in files_currently_in_archive:
                self.system_logger.warn(f"{file} already exists in deployment")
                duplicates += 1
            else:
                self.system_logger.info(f"{file} will be sent to the archive in non dry-run mode")
                files_added += 1

        self.system_logger.info(
            f"A total of {files_added} files would have been sent to the Archive in non dry-run mode"
        )
        self.system_logger.info(f"A total of {duplicates} duplicates were detected")

    def get_existing_glider_files_for_deployment(self) -> set:
        """Handle the call to the program which retrieves the set of existing glider filenames."""
        try:
            files_in_current_deployment = return_existing_glider_files(self.deployment_id)
        except HoldingsAccessError:
            files_in_current_deployment = set()
            self.system_logger.warn(
                "Unable to get existing files. Checks can't be done to ensure file is not already in archive."
            )
        else:
            self.system_logger.info(f"Filenames retrieved successfully for deployment: {self.deployment_id}")

        return files_in_current_deployment

    def _token_refresh(self) -> None:
        """Private method to refresh access token."""
        self.access_token = token_refresher_call(self.refresh_token, self.config)["access_token"]

    def send_files_to_api(self) -> None:
        """Manages the sending of files to the API."""
        files_currently_in_archive = self.get_existing_glider_files_for_deployment()
        files_to_send_to_archive = self.retrieve_file_paths()
        self.system_logger.info(f"The program will attempt to add {len(files_to_send_to_archive )} to the archive")

        self.system_logger.info(
            f"Currently {len(files_currently_in_archive)} files in archive for deploymentID: {self.deployment_id}"
        )

        duplicates, files_added = 0, 0
        for file in files_to_send_to_archive:  # pylint: disable=too-many-nested-blocks
            self.system_logger.info(f"Starting file transfer of {file} to BODC.")
            if file in files_currently_in_archive:
                duplicates += 1
                self.system_logger.warn(f"{file} already exists in deployment")
            else:
                attempts = 0
                while attempts < 3:
                    try:
                        response = send_to_archive_api(file, self.deployment_id, self.access_token)
                        if response == "Success":
                            files_added += 1
                            self.file_logger.write_to_log_file(str(file))
                            self.system_logger.info(f"File transfer complete for: {file}")
                            break
                    except AuthenticationError:
                        self.system_logger.warn("Auth failed, attempting to reset token")
                        self._token_refresh()
                    except FileUploadError:
                        self.system_logger.error(f"File transfer Failed for: {file}")
                    finally:
                        attempts += 1

        self.system_logger.info(
            f"There are {files_added + len(files_currently_in_archive)} files in archive after {files_added} new files"
        )
        self.system_logger.info(f"A total of {duplicates} duplicates were detected")
