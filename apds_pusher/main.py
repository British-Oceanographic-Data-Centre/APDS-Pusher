"""APDS command line tool"""
import click


def verify_cli_input(cli_input: str) -> bool:
    """Verifies the inputs and returns True if they are non empty strings."""
    return isinstance(cli_input, str) and len(cli_input) > 1



@click.command()
@click.option('--deployment_id', help='The Code/ID for the specific deployment.')
@click.option('--deployment_location', help='Full path to file directory.')
@click.option('--config_location', help='Full path to config file.')
@click.option('--non_production',
              default=False,
              show_default=True,
              help='Pass this flag to run the application in a non-production environment.')
@click.option('--dry_run',
              default=False,
              show_default=True,
              help='Pass this flag to perform a dry-run of the application.')
def cli_main(deployment_id: str,
             deployment_location : str,
             config_location: str,
             non_production: bool = False,
             dry_run: bool = False):
    
    argument_names = ['Deployment Id', 'Deployment Location', 'Config Location']

    program_arguments = [deployment_id,
                                  deployment_location,
                                  config_location]

    # Loop through the required arguments to perform verification
    for arg_name, arg in zip(argument_names, program_arguments):
        if not verify_cli_input(arg):
            print('{} is invalid'.format(arg_name))


if __name__ == '__main__':
    cli_main()