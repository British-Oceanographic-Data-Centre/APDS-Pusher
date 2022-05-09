"""APDS command line tool to perform simple verification of inputs."""
import json
import sys
from pathlib import Path

import click

from apds_pusher import config_parser, device_auth


def load_configuration_file(config_path: Path) -> config_parser.Configuration:
    """Load a configuration file JSON into a Configuration instance."""
    # load the json file or exit if it's bad
    try:
        config_dict = json.loads(config_path.read_text(encoding=sys.getdefaultencoding()))
    except json.JSONDecodeError:
        raise click.ClickException(f"Configuration failed to load from file: {config_path})") from None

    try:
        config = config_parser.Configuration.from_dict_validated(config_dict)
    except config_parser.ParserException as exc:
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
    help="Pass this flag to run the application in a non-production environment.",
)
@click.option(
    "--dry-run/--no-dry-run",
    "is_dry_run",
    default=False,
    show_default=True,
    help="Pass this flag to perform a dry-run of the application.",
)
def cli_main(
    deployment_id: str,
    data_directory: Path,
    config_file: Path,
    is_production: bool,
    is_dry_run: bool,
) -> None:
    """Accepts command line arguments and passes them to verification function."""
    del deployment_id, data_directory, is_production, is_dry_run
    config = load_configuration_file(config_file)
    # follow the Auth device flow to allow a user to log in via a 3rd party system
    device_code_dtls = device_auth.authenticate(config)
    click.echo(
        f"URL to authenticate: {device_code_dtls[0]} \
        \nUser_code : {device_code_dtls[1]} \
        \nexpires in: {device_code_dtls[2]} seconds"
    )


if __name__ == "__main__":
    cli_main()  # pylint: disable=no-value-for-parameter
