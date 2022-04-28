"""APDS command line tool to perform simple verification of inputs."""
import click


# Function left in simple state, to provide future scope for verification
# of deployment id, deployment location and config location if needed.
def verify_commandline_args(arguments: list) -> None:
    """Function is only called when all args successfully pass verification.

    Args:
        arguments: A list containing all args from the command line.
    """
    if arguments:
        print("Accepted")
    else:
        print("Refused")


click_dict = {
    "deployment_id": "The Code/ID for the specific deployment.",
    "deployment_location": "Full path to file directory.",
    "config_location": "Full path to config file.",
    "non_production": "Pass this flag to run the application in a non-production environment.",
    "dry_run": "Pass this flag to perform a dry-run of the application.",
}


def verify(_, param, value):
    """Verification callback function called by click decorators.

    Args:
        _: unused (this is sent by click)
        param: The parameter name, sent by click
        value: The argument to be validated
    Returns:
        The value will be returned only if validation passes.
    """
    param = param.human_readable_name
    if not (isinstance(value, str) and len(value) > 1):
        raise click.BadParameter(f"{param} entered incorrectly")
    return value


@click.command()
@click.option("--deployment_id", required=True, callback=verify, help=click_dict["deployment_id"])
@click.option("--deployment_location", required=True, callback=verify, help=click_dict["deployment_location"])
@click.option("--config_location", required=True, callback=verify, help=click_dict["config_location"])
@click.option("--non_production", default=False, show_default=True, help=click_dict["non_production"])
@click.option("--dry_run", default=False, show_default=True, help=click_dict["dry_run"])
def cli_main(
    deployment_id: str,
    deployment_location: str,
    config_location: str,
    non_production: bool = False,
    dry_run: bool = False,
):
    """Accepts command line arguments and passes them to verification function."""
    program_arguments = [deployment_id, deployment_location, config_location, non_production, dry_run]
    verify_commandline_args(program_arguments)


if __name__ == "__main__":
    cli_main()  # pylint: disable=no-value-for-parameter
