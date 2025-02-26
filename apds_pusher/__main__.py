"""APDS command line tool to perform simple verification of inputs."""

import sys
import traceback
from pathlib import Path

import click

from apds_pusher import device_auth, filepusher
from apds_pusher.get_version_info import get_current_version, get_github_tag_info, get_latest_install_command
from apds_pusher.systemlogger import SystemLogger
from apds_pusher.utils.deployment_utils import (
    check_add_active_deployments,
    check_delete_active_deployments,
    load_configuration_file,
)


class DeploymentNotFoundError(Exception):
    """Exception raised when trying to stop archival for Deployments that have not started ."""


class DeploymentError(Exception):
    """Exception raised when trying to start archival for Deployments."""


def verify_string_not_empty(_: click.Context, param: click.Parameter, value: str) -> str:
    """Verification callback function called by click decorators.

    Args:
        _: Context (unused), sent by click
        param: The parameter, sent by click
        value: The argument to be validated
    Returns:
        The value will be returned only if validation passes.
    """
    if value:
        return value

    raise click.BadParameter(f"{param.human_readable_name} must not be empty")


def initialise_system_logging() -> None:
    """Sets up the file and system logging."""
    return


# pylint: disable=R0917
def process_deployment(  # pylint: disable=too-many-arguments,too-many-locals
    deployment_id: str,
    data_directory: Path,
    config_file: Path,
    is_production: bool,
    is_dry_run: bool,
    is_recursive: bool,
    trace_on: bool,
    command: str,
) -> None:
    """Reusable function to handle start and recovery logic."""
    config = load_configuration_file(config_file)

    print(f"The trace is: {trace_on}")

    s_logger = SystemLogger(deployment_id, config.log_file_location, config.deployment_location, trace=trace_on)
    s_logger.debug("The system logger for %s has been setup!", deployment_id)
    s_logger.info("Current apds-pusher version: %s", get_current_version())

    result, deployment_file = check_add_active_deployments(deployment_id, config)

    if result:
        click.echo(f"{command.capitalize()} for deployment id {deployment_id}")

    # Follow the Auth device flow to allow a user to log in via a 3rd party system
    device_code_dtls = device_auth.authenticate(config)

    # Construct dictionary to hold data presented to end user for Authentication
    device_code_keys = ["url", "user_code", "expires_in", "device_code", "interval"]
    device_response = dict(zip(device_code_keys, device_code_dtls))

    click.echo(
        f"URL to authenticate: {device_response['url']} \n"
        f"User code: {device_response['user_code']} \n"
        f"Expires in: {device_response['expires_in']} seconds"
    )

    # Filter dictionary to send necessary keys to get access token
    response = {
        key: value for key, value in device_response.items() if key in ["device_code", "interval", "expires_in"]
    }

    # Send dictionary and config to complete authentication
    tokens = device_auth.receive_access_token_from_device_code(response, config)
    s_logger.debug("Auth setup complete")
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Call the file archival passing the access_token
    try:
        pusher = filepusher.FilePusher(
            deployment_id,
            data_directory,
            config,
            is_production,
            is_recursive,
            is_dry_run,
            access_token,
            refresh_token,
            deployment_file,
            s_logger,
            command,
        )
        s_logger.debug("Starting the pusher for %s using data from %s", deployment_id, data_directory)
        pusher.run()
    except Exception as e_obj:  # pylint: disable=broad-except
        s_logger.debug("An error happened on deploy %s using data from %s", deployment_id, data_directory)
        s_logger.error(str(e_obj))
        s_logger.debug(traceback.format_exc())


@click.group(invoke_without_command=True)
@click.option("--version", "version", flag_value=True, is_flag=True, show_default=True, help="display version info")
@click.pass_context
def pusher_group(ctx: click.Context, version: bool) -> None:
    """A group of all commands."""
    if version:
        current_version = get_current_version()
        latest_remote_version = get_github_tag_info()
        statement = f"Current version:\t{current_version}\nLatest version:\t\t{latest_remote_version}\n"
        click.echo(statement)
        if current_version != latest_remote_version:
            click.echo("To install the latest version, run the following command:")
            click.echo(f"\n\t{get_latest_install_command(latest_remote_version)}\n")
        sys.exit(0)
    if not version and not ctx.invoked_subcommand:
        click.echo("Error: Missing command.")
        sys.exit(1)


@click.option(
    "--deployment-id",
    required=True,
    type=str,
    callback=verify_string_not_empty,
    help="The Code/ID for the specific deployment.",
)
@click.option(
    "--data-directory",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Full path to the directory where files to be uploaded are stored.",
)
@click.option(
    "--config-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Full path to config file used for authentication.",
)
@click.option(
    "--production/--non-production",
    "is_production",
    default=False,
    show_default=True,
    help="Use this flag to switch between production and non-production environments.",
)
@click.option(
    "--dry-run/--no-dry-run",
    "is_dry_run",
    default=False,
    show_default=True,
    help="Use this flag to switch between a regular run and a dry run send of files.",
)
@click.option(
    "--recursive/--non-recursive",
    "is_recursive",
    default=False,
    show_default=True,
    help="Use this flag to switch between recursive and non-recursive searching of files.",
)
@click.option(
    "-t",
    "--trace",
    "trace_on",
    is_flag=True,
    default=False,
    show_default=True,
    help="Set app off in trace move (very verbos logging) or not (default is not)",
)
@click.command()
def start(  # pylint: disable=too-many-arguments, too-many-locals
    *,
    deployment_id: str,
    data_directory: Path,
    config_file: Path,
    is_production: bool,
    is_dry_run: bool,
    is_recursive: bool,
    trace_on: bool,
) -> None:
    """Accept command line arguments and passes them to verification function."""
    process_deployment(
        deployment_id, data_directory, config_file, is_production, is_dry_run, is_recursive, trace_on, "NRT"
    )


# to stop a deployment!
@click.command()
@click.option(
    "--deployment-id",
    required=True,
    type=str,
    callback=verify_string_not_empty,
    help="The Code/ID for the specific deployment to be removed.",
)
@click.option(
    "--config-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Full path to config file used for locating the active deployment directory.",
)
def stop(
    deployment_id: str,
    config_file: Path,
) -> None:
    """Accept command line arguments and stops archival for a deployment id."""
    click.echo(f"Stopping deployment id: {deployment_id}")
    config = load_configuration_file(config_file)
    s_logger = SystemLogger(deployment_id, config.log_file_location, config.deployment_location)
    s_logger.info(
        "The system logger for %s is noting that the deployment is being stopped via the stop command!",
        deployment_id,
    )
    if check_delete_active_deployments(deployment_id, config):
        s_logger.info("%s is now going to be stopped on the pusher.", deployment_id)
        click.echo(f"Archival for deployment id {deployment_id} will be stopped")


# when a glider or slocum is recovered
@click.option(
    "--deployment-id",
    required=True,
    type=str,
    callback=verify_string_not_empty,
    help="The ID for the specific deployment being recovered.",
)
@click.option(
    "--data-directory",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Full path to the directory to pick the zipped files from.",
)
@click.option(
    "--config-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Full path to config file used for authentication.",
)
@click.option(
    "--production/--non-production",
    "is_production",
    default=False,
    show_default=True,
    help="Use this flag to switch between production and non-production environments.",
)
@click.option(
    "--dry-run/--no-dry-run",
    "is_dry_run",
    default=False,
    show_default=True,
    help="Use this flag to switch between a regular run and a dry run send of files.",
)
@click.option(
    "--recursive/--non-recursive",
    "is_recursive",
    default=True,
    show_default=True,
    help="Use this flag to switch between recursive and non-recursive searching of files.",
)
@click.option(
    "-t",
    "--trace",
    "trace_on",
    is_flag=True,
    default=False,
    show_default=True,
    help="Set app off in trace move (very verbos logging) or not (default is not)",
)
@click.command()
def recovery(  # pylint: disable=too-many-arguments
    *,
    deployment_id: str,
    data_directory: Path,
    config_file: Path,
    is_production: bool,
    is_dry_run: bool,
    is_recursive: bool,
    trace_on: bool,
) -> None:
    """Accept command line arguments and passes them to verification function."""
    process_deployment(
        deployment_id, data_directory, config_file, is_production, is_dry_run, is_recursive, trace_on, "Recovery"
    )


pusher_group.add_command(start)
pusher_group.add_command(stop)
pusher_group.add_command(recovery)

if __name__ == "__main__":
    pusher_group()  # pylint: disable=no-value-for-parameter
