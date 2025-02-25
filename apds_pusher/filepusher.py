"""Program to orchestrate push of files to the Archive API."""

import time
import traceback
from datetime import datetime
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

    # pylint: disable=R0913,R0917
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
        deployment_file: Path,
        log: SystemLogger,
        mode:str
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
        self.deployment_file = deployment_file
        self.system_logger = log
        self.mode = mode

        # Begin the logging
        self.initialise_logging()
        self.system_logger.debug("Finished the setup of the FilePusher class")

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
            try:
                self.system_logger.debug(f"starting loop for deployment {self.deployment_id}")
                # start archival if there was no request to stop the archival
                if self.check_deployment_not_stopped(self.deployment_id):
                    self.system_logger.info(f"Starting cycle number: {file_push_cycles}")

                    if self.is_dry_run:
                        self.system_logger.debug(f"{self.deployment_id} is set to dry run")
                        self.dry_run_send(file_push_cycles)
                    else:
                        self.system_logger.debug(f"{self.deployment_id} will be sending files to BODC's Archive API")
                        self.send_files_to_api(file_push_cycles)

                    self.system_logger.info(f"Cycle number {file_push_cycles} complete.")
                    file_push_cycles += 1
                    self.system_logger.debug(f"Moving to cycle number {file_push_cycles}.")
                    self.system_logger.debug("sleep starting")
                    sleep(self.config.archive_checker_frequency * 60)
                    self.system_logger.debug("sleep over")
                else:
                    self.system_logger.debug(f"{self.deployment_id} has failed the check_deployment_not_stopped check")
                    self.system_logger.info("'check_deployment_not_stopped' returned False, program exiting.")
                    raise SystemExit
            except Exception as e_obj:  # pylint: disable=broad-except
                # Log the full traceback to the system logger.
                self.system_logger.error(f"Exception caught during file send loop: {traceback.format_exc()}")
                self.system_logger.debug("Unknown error has happen.")
                self.system_logger.debug(f"{str(e_obj)}.")

                # For clarity, write the full traceback to its own file.
                with open(f"Error_cycle_{file_push_cycles}.txt", mode="w", encoding="utf-8") as error_file:
                    error_file.write(traceback.format_exc())

                file_push_cycles += 1
                self.system_logger.debug(f"Moving to cycle number {file_push_cycles}.")

    def check_deployment_not_stopped(self, deployment_id: str) -> bool:
        """Check if there was a request to stop the archival for the deployment id."""
        active_deployments_location = self.config.deployment_location
        deployment_id_file = active_deployments_location / f"{deployment_id}.txt"
        return deployment_id_file.exists()

    def initialise_logging(self) -> None:
        """Sets up the file and system logging."""
        self.file_logger = FileLogger(self.config.save_file_location, self.deployment_location, self.deployment_id)
        self.system_logger.info(f"File Logger located at: {self.file_logger.file_path}")

    def retrieve_file_paths(self, cycle_number: int) -> List[Path]:
        """Retrieve a list of absolute paths for desired glider files."""
        self.system_logger.debug(f"Starting glider file search for {self.deployment_id} on cycle {cycle_number}")
        recursive_state = "Active" if self.is_recursive else "Not active"
        self.system_logger.info(f"Recursive folder searching is {recursive_state}")

        self.system_logger.debug("Opening deployment file to look for last run time")
        with open(Path(self.deployment_file), "r", encoding="utf-8") as deployment_file:
            deployment_time = float(deployment_file.read())
            self.system_logger.debug(f"deployment time is: {deployment_time}")
            self.system_logger.debug(f"which in machine local time is {datetime.fromtimestamp(deployment_time)}")
            self.system_logger.debug(f"which in UTC is {datetime.utcfromtimestamp(deployment_time)} ")

        file_paths: List[Path] = []
        self.system_logger.debug(f"file_paths start as empty: {file_paths}")
        glob_prefix = "**/*" if self.is_recursive else "*"
        self.system_logger.debug(f"search prefix is set to: {glob_prefix}")
        self.system_logger.debug(f"searching for the the following formats: {self.config.file_formats}")
        for file_format in self.config.file_formats:
            unfiltered = list(self.deployment_location.glob(f"{glob_prefix}{file_format}"))
            self.system_logger.debug(f"unfiltered set of files for {file_format} is: {str(unfiltered)}")
            if not unfiltered:
                self.system_logger.debug(f"No files found for {file_format}")
                continue

            if cycle_number > 1:
                self.system_logger.debug(f"{cycle_number} is greater than 1 - this mean we will filter results")
                file_paths.extend(list(filter(lambda file: file.lstat().st_mtime > deployment_time, unfiltered)))
            else:
                self.system_logger.debug(f"{cycle_number} is less than 1 - this mean we will not filter results")
                file_paths.extend(unfiltered)

        self.system_logger.debug(f"checking the final object: {str(file_paths)}")
        return file_paths

    def dry_run_send(self, cycle_number: int) -> None:
        """Perform a dry run send of the files."""
        self.system_logger.debug(f"Starting dry run for {self.deployment_id}")
        files_currently_in_archive = self.get_existing_glider_files_for_deployment()
        duplicates, files_added = 0, 0
        self.system_logger.info(f"Starting a dry run for deployment id: {self.deployment_id}")
        self.system_logger.info(f"There are currently {len(files_currently_in_archive)} files in the BODC archive.")

        for file in self.retrieve_file_paths(cycle_number):
            if file.name in files_currently_in_archive:
                self.system_logger.warn(f"{file} already exists in deployment")
                duplicates += 1
            else:
                self.system_logger.info(f"{file} will be sent to the archive in non dry-run mode")
                files_added += 1

        self.system_logger.info(
            f"A total of {files_added} files would have been sent to the BODC archive in non dry-run mode"
        )
        self.update_timestamp_in_deployment_file()
        self.system_logger.info("Time updated for the next push.")
        self.system_logger.info(f"A total of {duplicates} duplicates were detected")

    def get_existing_glider_files_for_deployment(self) -> set:
        """Handle the call to the program which retrieves the set of existing glider filenames."""
        self.system_logger.debug(f"Starting fetch for glider file names for {self.deployment_id}")
        try:
            self.system_logger.debug(
                f"Calling bodc archive endpoint to " f"get list of files BODC already hold for {self.deployment_id}"
            )
            files_in_current_deployment = return_existing_glider_files(self.config.bodc_archive_url, self.deployment_id)
        except HoldingsAccessError as hae:
            self.system_logger.debug(f"Error for: {self.deployment_id} which is: {str(hae)}")
            self.system_logger.error(
                "Unable to get existing files. A file send will not be attempted to avoid sending duplicated files."
            )
            self.system_logger.debug(f"Full Traceback for holdings endpoint error: {traceback.format_exc()}")
            raise HoldingsAccessError from None

        self.system_logger.info(f"Filenames retrieved successfully for deployment: {self.deployment_id}")
        return files_in_current_deployment

    def _token_refresh(self) -> None:
        """Private method to refresh access token."""
        self.access_token = get_access_token_from_refresh_token(self.refresh_token, self.config)

    def update_timestamp_in_deployment_file(self) -> None:
        """Update timestamp in the DEP.txt file.

        This method is called after each file send loop, and when called
        it will write the current timestamp to each file.

        """
        self.system_logger.debug(f"Opening deployment file @ {str(Path(self.deployment_file))} for changing time")
        current_time = time.time()
        self.system_logger.debug(f"Current time set at: {current_time}")
        self.system_logger.debug(f"which in machine local time is {datetime.fromtimestamp(current_time)}")
        self.system_logger.debug(f"which in UTC is {datetime.utcfromtimestamp(current_time)} ")

        with open(Path(self.deployment_file), "w", encoding="utf-8") as file:
            file.write(str(current_time))

    def send_files_to_api(self, cycle_number: int) -> None:  # pylint: disable=R0912, R0915, too-many-locals
        """Manages the sending of files to the API."""
        self.system_logger.debug(f"Starting file push for {self.deployment_id}")
        try:
            files_currently_in_archive = self.get_existing_glider_files_for_deployment()
        except HoldingsAccessError as hae:
            self.system_logger.debug("An error has happen on the holding Access")
            self.system_logger.debug(f"{str(hae)}.")
            return

        files_to_send_to_archive = self.retrieve_file_paths(cycle_number)
        self.system_logger.info(f"There are {len(files_to_send_to_archive )} files locally")

        self.system_logger.info(
            f"There are currently {len(files_currently_in_archive)} "
            f"files in BODC archive for deploymentID: {self.deployment_id}"
        )
        duplicates, files_added = 0, 0
        for file in files_to_send_to_archive:  # pylint: disable=too-many-nested-blocks
            self.system_logger.info(f"Starting file transfer of {file} to BODC.")
            if file.name in files_currently_in_archive:
                duplicates += 1
                self.system_logger.warn(f"{file} already exists in deployment")
            else:
                attempts = 0
                self.system_logger.debug(f"Attempt {attempts}.")
                while attempts < 3:
                    try:
                        response = send_to_archive_api(
                            file, self.deployment_id, self.access_token, self.config.bodc_archive_url, self.mode,self.system_logger
                        )
                        if response == "Success":
                            self.system_logger.debug("ok")
                            files_added += 1
                            self.file_logger.write_to_log_file(str(file))
                            self.system_logger.info(f"File transfer complete for: {file}")
                            break
                    except AuthenticationError as ae_obj:
                        self.system_logger.warn("Auth failed, attempting to reset token")
                        self.system_logger.debug(f"{str(ae_obj)}")
                        self.system_logger.debug("There was an error with the token: lets refresh")
                        self._token_refresh()
                        self.system_logger.debug("Ok we have done the refresh")

                    except FileUploadError as fue_obj:
                        self.system_logger.error(f"File transfer Failed for: {file}")
                        self.system_logger.debug(f"{str(fue_obj)}")
                    except ConnectTimeout as exc_obj:
                        self.system_logger.error(f"Connection timed out during transfer of {file}")
                        if exc_obj.request:
                            self.system_logger.error(
                                f"This attempt failed with the following full URL: {exc_obj.request.url}"
                            )
                        self.system_logger.error(
                            f"This attempt failed with the following output: {traceback.format_exc()}"
                        )
                        self.system_logger.debug(f"{str(exc_obj)}")
                    except ConnectionError as ce_obj:
                        self.system_logger.error(
                            f"Failed to connect to {self.config.bodc_archive_url} during transfer of {file}"
                        )
                        self.system_logger.error(
                            f"This attempt failed with the following output: {traceback.format_exc()}"
                        )
                        self.system_logger.debug(f"{str(ce_obj)}")
                    except RequestException as re_obj:
                        self.system_logger.error(
                            f"Failed to connect to {self.config.bodc_archive_url} during transfer of {file}"
                        )
                        self.system_logger.error(
                            f"This attempt failed with the following output: {traceback.format_exc()}"
                        )
                        self.system_logger.debug(f"{str(re_obj)}")
                    except Exception as e_obj:  # pylint: disable=broad-except
                        self.system_logger.debug("This is a catch all then:")
                        self.system_logger.debug(f"{str(e_obj)}")
                        self.system_logger.error(
                            f"This attempt failed with the following output: {traceback.format_exc()}"
                        )
                        break
                    finally:
                        attempts += 1
                        self.system_logger.debug(f"Oh dear something went wrong now on {attempts}.")

        self.system_logger.info(
            f"There are {files_added + len(files_currently_in_archive)} files in archive after {files_added} new files"
        )
        self.system_logger.debug("about to set new time in deployment file")
        self.update_timestamp_in_deployment_file()
        self.system_logger.debug("Have set new time in deployment file")
        self.system_logger.info("Time updated for the next push.")
        self.system_logger.info(f"A total of {duplicates} duplicates were detected")
