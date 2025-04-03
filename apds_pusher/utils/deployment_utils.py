"""utilities for file pusher."""

import json
import sys
import time
from pathlib import Path

import click

from apds_pusher.config_parser import Configuration, ParserException


class DeploymentNotFoundError(Exception):
    """Exception raised when trying to stop archival for Deployments that have not started ."""


class DeploymentError(Exception):
    """Exception raised when trying to start archival for Deployments."""


def check_delete_active_deployments(deployment_id: str, config: Configuration) -> bool:
    """Checks and deletes if archival for a deployment is going on.

    Args:
        deployment_id: The deployment id to be stopped
        config:  the config dict to locate the directory of active deployments
    Returns:
        True if it found the deployment id else raises error..
    """
    active_deployments_location = config.deployment_location
    if any(active_deployments_location.iterdir()):
        deployment_id_file = active_deployments_location / f"{deployment_id}.txt"

        try:
            if deployment_id_file.exists():
                deployment_id_file.unlink()
                return True
            raise DeploymentNotFoundError(f"Cannot stop. No archival started for deployment_id {deployment_id}")

        except FileNotFoundError as file_err:
            raise DeploymentNotFoundError(
                f"Cannot stop. No archival started for deployment_id {deployment_id}"
            ) from file_err

    else:
        # No archival has begun till now at all.
        raise DeploymentNotFoundError("No deployments being archived.")


def check_add_active_deployments(deployment_id: str, config: Configuration) -> tuple[bool, Path]:
    """Checks and adds if archival for a deployment is going on.

    Args:
        deployment_id: The deployment id to be stopped
        config:  the config dict to locate the directory of active deployments
    Returns:
        True if it the deployment id is added else raises error..
    """
    active_deployments_location = config.create_deployment_location()
    deployment_id_file = active_deployments_location / f"{deployment_id}.txt"

    # Causes the program to Error because the pusher app has already been started, therefore archival in progress.
    if Path(deployment_id_file).is_file():
        raise DeploymentError(f"Cannot re-start. Archival is going on for deployment_id {deployment_id}")

    Path(deployment_id_file).touch(exist_ok=False)

    with open(Path(deployment_id_file), "a", encoding="utf-8") as file:
        current_time = time.time()
        file.write(str(current_time))

    return True, deployment_id_file


def load_configuration_file(config_path: Path) -> Configuration:
    """Load a configuration file JSON into a Configuration instance."""
    # load the json file or exit if it's bad
    try:
        config_dict = json.loads(config_path.read_text(encoding=sys.getdefaultencoding()))
    except json.JSONDecodeError:
        raise click.ClickException(f"Configuration failed to load from file: {config_path}") from None

    try:
        config = Configuration.from_dict_validated(config_dict)
    except ParserException as exc:
        raise click.ClickException(exc.args[0]) from None

    if not isinstance(config.archive_checker_frequency, int):
        raise click.ClickException("'archive_checker_frequency' in the config file needs to be a integer.") from None

    click.echo(message="Configuration accepted")

    return config
