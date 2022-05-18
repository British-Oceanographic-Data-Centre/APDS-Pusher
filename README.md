# APDS-Pusher

This application allows organisations to continuously push data to the BODC archive from the command line.

-------

## Installation instructions

This section will walk you through the basic steps to install `APDS-Pusher`, including:

1. Checking your Python version,
2. Creating a virtual environment to run the tool, and
3. Installing the tool itself.

### Python version

`APDS-Pusher` requires Python 3.8 or higher to run.
To check the version of Python you are using, type the following command in the terminal:

```shell
$ python --version
```

If your version of Python is below 3.8 (or you don't have Python installed),
you will need to install a newer version of [Python](https://www.python.org/).

### Creating a virtual environment

In order to isolate the installation of `APDS-Pusher` from your other software, it is recommended that it be installed in its own virtual environment.

To create a virtual environment called `venv`, first navigate to the location you wish to create
the virtual environment in on your system, and then run the following command:

```shell
$ python -m venv venv
```

You then need to activate the virtual environment as follows:

Linux:

```shell
$ . ./venv/bin/activate
```

Windows:

```shell
$ . ./venv/Scripts/activate
```

### Installing APDS-Pusher

Now that the virtual environment is activated, you can install `APDS-Pusher` and specify the
version you would like to install (in the example below the version is `v1.2.3`):

```shell
(venv) $ python -m pip install git+https://github.com/British-Oceanographic-Data-Centre/APDS-Pusher@v1.2.3
```

Available versions can be found on the
[Releases](https://github.com/British-Oceanographic-Data-Centre/APDS-Pusher/releases)
page of the `APDS-Pusher` GitHub repository.

You can check that it is installed correctly by now running:

```shell
(venv) $ bodc-archive-pusher --help
```

This should display the help for the tool (see also next section) if it is installed correctly.

-------

## Usage instructions

[//]: # (This is output from the CLI --help command and should be kept up-to-date with that output)

```
Usage: bodc-archive-pusher [OPTIONS]

  This application allows organisations to continuously push data to BODC from
  the command line.

Options:
  --deployment-id TEXT            The Code/ID for the specific deployment.
                                  [required]
  --data-directory DIRECTORY      Full path to the directory where files to be
                                  uploaded are stored. This directory will be
                                  searched recursively for files to send.
                                  [required]
  --config-file FILE              Full path to configuration file controlling
                                  the running of the application.  [required]
  --production / --non-production
                                  Pass this flag to toggle between pushing
                                  data to the production or non-production
                                  (test) systems.  [default: non-production]
  --dry-run / --no-dry-run        Pass this flag to perform a dry-run of the
                                  application. This mode will imitate a
                                  transfer but will only print the files to be
                                  sent, and not send them.  [default: no-dry-
                                  run]
  --help                          Show this message and exit.
```
