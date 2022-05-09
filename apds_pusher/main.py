"""APDS command line tool to perform simple verification of inputs."""
import json
import sys
from pathlib import Path
from typing import Any

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


param_meanings = {
    "deployment_id": "The Code/ID for the specific deployment.",
    "deployment_location": "Full path to file directory where files to be uploaded are stored.",
    "config_location": "Full path to config file used for authentication.",
    "non_production": "Pass this flag to run the application in a non-production environment.",
    "dry_run": "Pass this flag to perform a dry-run of the application.",
}


def verify_string_not_empty(_: click.Context, param: click.Parameter, value: Any) -> str:
    """Verification callback function called by click decorators.

    Args:
        _: Context (unused), sent by click
        param: The parameter, sent by click
        value: The argument to be validated
    Returns:
        The value will be returned only if validation passes.
    """
    if not (isinstance(value, str) and len(value) > 1):
        raise click.BadParameter(f"{param.human_readable_name} entered incorrectly")
    return value


@click.command()
@click.option("--deployment_id", required=True, callback=verify_string_not_empty, help=param_meanings["deployment_id"])
@click.option(
    "--deployment_location", required=True, callback=verify_string_not_empty, help=param_meanings["deployment_location"]
)
@click.option(
    "--config_location",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help=param_meanings["config_location"],
)
@click.option("--non_production", default=False, show_default=True, help=param_meanings["non_production"])
@click.option("--dry_run", default=False, show_default=True, help=param_meanings["dry_run"])
def cli_main(
    deployment_id: str,
    deployment_location: str,
    config_location: Path,
    non_production: bool,
    dry_run: bool,
) -> None:
    """Accepts command line arguments and passes them to verification function."""
    del deployment_id, deployment_location, non_production, dry_run
    config = load_configuration_file(config_location)
    # follow the Auth device flow to allow a user to log in via a 3rd party system
    device_code_dtls = device_auth.authenticate(config)
    click.echo(
        f"URL to authenticate: {device_code_dtls[0]} \
        \nUser_code : {device_code_dtls[1]} \
        \nexpires in: {device_code_dtls[2]} seconds"
    )


if __name__ == "__main__":
    cli_main()  # pylint: disable=no-value-for-parameter
