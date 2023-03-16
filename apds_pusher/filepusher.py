"""Program to orchestrate push of files to the Archive API."""
import traceback
from pathlib import Path
from time import sleep
from typing import List

from requests.exceptions import ConnectTimeout, RequestException

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
from apds_pusher.token_refresher import get_access_token_from_refresh_token


class FilePusher:  # pylint: disable=too-many-instance-attributes
    """Class for managing interaction with Archive API."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        deployment_id: str,
        deployment_location: Path,
        config: Configuration,
        is_production: bool,
        is_recursive: bool,
        is_dry_run: bool,
        access_token: str,
        refresh_token: str,
    ):
        """Setup for File Pusher."""
        self.deployment_id = deployment_id
        self.deployment_location = deployment_location
        self.config = config
        self.is_production = is_production
        self.is_recursive = is_recursive
        self.is_dry_run = is_dry_run
        self.access_token = access_token
        self.refresh_token = refresh_token

        # Begin the logging
        self.initialise_logging()

    def run(self) -> None:
        """Trigger a loop which controls sending files or a dry run.

        archive_checker_frequency is determined in the config file.
        The program is designed to perform a send of files, wait
        for x minutes and perform a new send.
        """
        self.system_logger.info(
            f"Program will wait {self.config.archive_checker_frequency} minutes between checking for new files."
        )
        file_push_cycles = 1

        while True:
            # start archival if there was no request to stop the archival
            if self.check_deployment_not_stopped(self.deployment_id):
                self.system_logger.info(f"Starting cycle number: {file_push_cycles}")

                if self.is_dry_run:
                    self.dry_run_send()
                else:
                    self.send_files_to_api()

                self.system_logger.info(f"Cycle number {file_push_cycles} complete.")
                file_push_cycles += 1
                sleep(self.config.archive_checker_frequency * 60)
            else:
                raise SystemExit

    def check_deployment_not_stopped(self, deployment_id: str) -> bool:
        """Check if there was a request to stop the archival for the deployment id."""
        active_deployments_location = self.config.deployment_location
        deployment_id_file = active_deployments_location / f"{deployment_id}.txt"
        return deployment_id_file.exists()

    def initialise_logging(self) -> None:
        """Sets up the file and system logging."""
        self.system_logger = SystemLogger(self.deployment_id, self.config.log_file_location, self.deployment_location)
        self.file_logger = FileLogger(self.config.save_file_location, self.deployment_location, self.deployment_id)
        self.system_logger.info(f"Save file located at: {self.file_logger.file_path}")

    def retrieve_file_paths(self) -> List[Path]:
        """Retrieve a list of absolute paths for desired glider files."""
        recursive_state = "Active" if self.is_recursive else "Not active"
        self.system_logger.info(f"Recursive folder searching is {recursive_state}")

        file_paths: List[Path] = []
        glob_prefix = "**/*" if self.is_recursive else "*"
        for file_format in self.config.file_formats:
            file_paths.extend(self.deployment_location.glob(f"{glob_prefix}{file_format}"))

        return file_paths

    def dry_run_send(self) -> None:
        """Perform a dry run send of the files."""
        files_currently_in_archive = self.get_existing_glider_files_for_deployment()
        duplicates, files_added = 0, 0
        self.system_logger.info(f"Starting a dry run for deployment id: {self.deployment_id}")
        self.system_logger.info(f"There are currently {len(files_currently_in_archive)} files in the BODC archive.")

        for file in self.retrieve_file_paths():
            if file.name in files_currently_in_archive:
                self.system_logger.warn(f"{file} already exists in deployment")
                duplicates += 1
            else:
                self.system_logger.info(f"{file} will be sent to the archive in non dry-run mode")
                files_added += 1

        self.system_logger.info(
            f"A total of {files_added} files would have been sent to the BODC archive in non dry-run mode"
        )
        self.system_logger.info(f"A total of {duplicates} duplicates were detected")

    def get_existing_glider_files_for_deployment(self) -> set:
        """Handle the call to the program which retrieves the set of existing glider filenames."""
        try:
            files_in_current_deployment = return_existing_glider_files(self.config.bodc_archive_url, self.deployment_id)
        except HoldingsAccessError:
            self.system_logger.error(
                "Unable to get existing files. A file send will not be attempted to avoid sending duplicated files."
            )
            self.system_logger.error(f"Full Traceback for holdings endpoint error: {traceback.format_exc()}")
            raise HoldingsAccessError from None
        else:
            self.system_logger.info(f"Filenames retrieved successfully for deployment: {self.deployment_id}")

        return files_in_current_deployment

    def _token_refresh(self) -> None:
        """Private method to refresh access token."""
        self.access_token = get_access_token_from_refresh_token(self.refresh_token, self.config)

    def send_files_to_api(self) -> None:  # pylint: disable=R0912
        """Manages the sending of files to the API."""
        try:
            files_currently_in_archive = self.get_existing_glider_files_for_deployment()
        except HoldingsAccessError:
            return
        files_to_send_to_archive = self.retrieve_file_paths()
        self.system_logger.info(f"There are {len(files_to_send_to_archive )} files locally")

        self.system_logger.info(
            f"There are currently {len(files_currently_in_archive)} files in BODC archive for deploymentID: {self.deployment_id}"
        )

        duplicates, files_added = 0, 0
        for file in files_to_send_to_archive:  # pylint: disable=too-many-nested-blocks
            self.system_logger.info(f"Starting file transfer of {file} to BODC.")
            if file.name in files_currently_in_archive:
                duplicates += 1
                self.system_logger.warn(f"{file} already exists in deployment")
            else:
                attempts = 0
                while attempts < 3:
                    try:
                        response = send_to_archive_api(
                            file, self.deployment_id, self.access_token, self.config.bodc_archive_url
                        )
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
                    except ConnectTimeout as exc:
                        self.system_logger.error(f"Connection timed out during transfer of {file}")
                        self.system_logger.error(f"This attempt failed with the following full URL: {exc.request.url}")
                        self.system_logger.error(
                            f"This attempt failed with the following output: {traceback.format_exc()}"
                        )
                    except ConnectionError:
                        self.system_logger.error(
                            f"Failed to connect to {self.config.bodc_archive_url} during transfer of {file}"
                        )
                        self.system_logger.error(
                            f"This attempt failed with the following output: {traceback.format_exc()}"
                        )
                    except RequestException:
                        self.system_logger.error(
                            f"Failed to connect to {self.config.bodc_archive_url} during transfer of {file}"
                        )
                        self.system_logger.error(
                            f"This attempt failed with the following output: {traceback.format_exc()}"
                        )
                    finally:
                        attempts += 1

        self.system_logger.info(
            f"There are {files_added + len(files_currently_in_archive)} files in archive after {files_added} new files"
        )
        self.system_logger.info(f"A total of {duplicates} duplicates were detected")
