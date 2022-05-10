"""Program to orchestrate push of files to the Archive API."""
from pathlib import Path
from typing import List

from apds_pusher.config_parser import Configuration
from apds_pusher.savefilelogger import FileLogger
from apds_pusher.systemlogger import SystemLogger


def retrieve_glider_file_paths(folder_location: Path, file_formats: List[str]) -> List[Path]:
    """Retrieves a list of absolute paths for desired glider files.

    Args:
        folder_location: The path to be searched for glider files
        file_formats: The list of formats ensures only the correct gliders are selected.

    Returns:
        A list containing the absolute path to each desired glider, ready for upload.
    """
    file_paths = []

    for file_format in file_formats:
        for path in Path(folder_location).rglob(f"*{file_format}"):
            file_paths.append(path)

    return file_paths


def send_files_to_archive(
    files_to_send: List[Path], dry_run: bool, non_production: bool, file_logger: FileLogger, system_logger: SystemLogger
) -> None:
    """In progress."""
    non_prod_state = "Active" if non_production else "Inactive"
    dry_run_state = "Active" if dry_run else "Inactive"
    system_logger.info(f"Non production mode is {non_prod_state}")
    system_logger.info(f"Dry run mode is {dry_run_state}")

    for file in files_to_send:
        if dry_run:
            system_logger.info(f"File: {file} will be sent if running in non Dry-Run mode.")
        else:
            system_logger.info(f"Starting file transfer of {file} to BODC.")
            # # Routine to use Archive API to be ran here.
            file_logger.write_to_log_file(str(file))
            system_logger.info(f"File transfer complete for: {file}")


def file_push_procedure(  # pylint: disable=R0913
    deployment_id: str,
    deployment_location: Path,
    config: Configuration,
    non_production: bool,
    dry_run: bool,
) -> None:
    """Driver function to control sending of files to API.

    Args:
       deployment_id: The id for the deployment being sent to BODC.
       deployment_location: The location of the glider files to be sent.
       config: A Dataclass containing variables in the config file.
       non_production: A boolean flag. True indicates that files are sent to non-prod environent.
       dry_run: A boolean flag. When True, it will only print which files will be sent.
    """
    # Initialize the system logger
    system_logger = SystemLogger(deployment_id, Path(config.log_file_location), deployment_location)

    # Initialize the save-file logger
    file_logger = FileLogger(Path(config.save_file_location), deployment_location, deployment_id)
    system_logger.info(f"Save file located at: {file_logger.file_path}")

    # Use the formats to search through directory, to get all file paths
    glider_file_names = retrieve_glider_file_paths(deployment_location, config.file_formats)

    send_files_to_archive(glider_file_names, dry_run, non_production, file_logger, system_logger)
