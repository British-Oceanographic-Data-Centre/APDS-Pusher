"""APDS command line tool"""
import click


# Verification has been left simplified for the time being - jamclar 28/04/2022
def verify_cli_input(cli_input: str) -> bool:
    """Verifies individual inputs and returns True if they are non empty strings.
    
        Args:
            cli_input (str): the inputs sent from the command line.

        returns:
            True/False
    """


    return isinstance(cli_input, str) and len(cli_input) > 1


def verify_command_line_arguments(program_arguments: list) -> bool:
    """Verification function for all inputs.
    
    This function accepts all command line arguments as a list, and then
    verifies the 3 required arguments. It will print 'Accepted' if the arguments
    are acceptable, otherwise it will print 'Refused'.

    Args:
        program_arguments (list): a list containing all command line arguments

    Returns:
        A string -> Accepted/Refused
    """
    verification = all([verify_cli_input(arg) for arg in program_arguments[:3]])
    message = 'Accepted' if verification else 'Refused'
    print(message)


click_dict = {'deployment_id' : 'The Code/ID for the specific deployment.',
              'deployment_location' : 'Full path to file directory.',
              'config_location' : 'Full path to config file.',
              'non_production' : 'Pass this flag to run the application in a non-production environment.',
              'dry_run' : 'Pass this flag to perform a dry-run of the application.'}

@click.command()
@click.option('--deployment_id', required=True, type=str, help=click_dict['deployment_id'])
@click.option('--deployment_location', required=True, type=str, help=click_dict['deployment_location'])
@click.option('--config_location', required=True, type=str, help=click_dict['config_location'])
@click.option('--non_production', default=False, show_default=True, help=click_dict['non_production'])
@click.option('--dry_run', default=False, show_default=True, help=click_dict['dry_run'])
def cli_main(deployment_id: str,
             deployment_location : str,
             config_location: str,
             non_production: bool = False,
             dry_run: bool = False):
    """Accepts command line arguments and passes them to verification function."""
    program_arguments = [deployment_id, deployment_location, config_location, non_production, dry_run]
    verify_command_line_arguments(program_arguments)


if __name__ == "__main__":
    cli_main()

