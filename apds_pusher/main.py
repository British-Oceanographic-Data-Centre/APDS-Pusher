"""APDS Python Command Line Options Program."""
import click


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
    print(deployment_id)
    print(deployment_location)
    print(config_location)
    print(non_production)
    print(dry_run)



if __name__ == '__main__':
    cli_main()