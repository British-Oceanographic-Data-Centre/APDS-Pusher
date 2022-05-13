# APDS-Pusher

This application allows organisations to continuously push data to the BODC archive from the command line.

-------

## Installation instructions

It is recommended to create a new Python virtual environment to install the APDS-Pusher CLI tool into. Note that the command line tool expects Python 3.8 or higher.

-------

## Usage instructions

[//]: # (This is output from the CLI --help command and should be kept up-to-date with that output)

```
Usage: bodc-apds-pusher [OPTIONS]

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
