"""APDS command line tool to perform simple verification of inputs."""
import json
import sys
from pathlib import Path

import click

from apds_pusher import device_auth, filepusher
from apds_pusher.config_parser import Configuration, ParserException


def load_configuration_file(config_path: Path) -> Configuration:
    """Load a configuration file JSON into a Configuration instance."""
    # load the json file or exit if it's bad
    try:
        config_dict = json.loads(config_path.read_text(encoding=sys.getdefaultencoding()))
    except json.JSONDecodeError:
        raise click.ClickException(f"Configuration failed to load from file: {config_path})") from None

    try:
        config = Configuration.from_dict_validated(config_dict)
    except ParserException as exc:
        raise click.ClickException(exc.args[0]) from None

    click.echo(message="Configuration accepted")

    return config


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


@click.command()
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
    default=True,
    show_default=True,
    help="Use this flag to switch between recursive and non-recursive searching of files.",
)
def cli_main(  # pylint: disable=too-many-arguments
    deployment_id: str,
    data_directory: Path,
    config_file: Path,
    is_production: bool,
    is_dry_run: bool,
    is_recursive: bool,
) -> None:
    """Accept command line arguments and passes them to verification function."""
    config = load_configuration_file(config_file)
    # follow the Auth device flow to allow a user to log in via a 3rd party system
    device_code_dtls = device_auth.authenticate(config)

    # Construct dictionary to hold data presented to end user for Authenticationm
    device_code_keys = ["url", "user_code", "expires_in", "device_code", "interval"]
    device_response = dict(zip(device_code_keys, device_code_dtls))

    click.echo(
        f"URL to authenticate: {device_response['url']} \
        \nUser code: {device_response['user_code']} \
        \nExpires in: {device_response['expires_in']} seconds"
    )

    # Filter dictionary to send necessary keys to get access token
    response = {
        key: value for key, value in device_response.items() if key in ["device_code", "interval", "expires_in"]
    }

    # Send dictionary and config to complete authentication
    tokens = device_auth.receive_access_token_from_device_code(response, config)
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # call the file archival passing the access_token
    pusher = filepusher.FilePusher(
        deployment_id, data_directory, config, is_production, is_recursive, is_dry_run, access_token, refresh_token
    )
    pusher.run()


if __name__ == "__main__":
    cli_main()  # pylint: disable=no-value-for-parameter
