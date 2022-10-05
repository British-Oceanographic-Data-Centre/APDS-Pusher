APDS-Pusher
===========

This application allows organisations to continuously push data to the
BODC archive from the command line.

--------------

Installation instructions
-------------------------

This section will walk you through the basic steps to install
``APDS-Pusher``, including:

1. Checking your Python version,
2. Creating a virtual environment to run the tool, and
3. Installing the tool itself.

Python version
~~~~~~~~~~~~~~

``APDS-Pusher`` requires Python 3.8 or higher to run. To check the
version of Python you are using, type the following command in the
terminal:

.. code:: shell

   $ python --version

If your version of Python is below 3.8 (or you don't have Python
installed), you will need to install a newer version of
`Python <https://www.python.org/>`__.

Creating a virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to isolate the installation of ``APDS-Pusher`` from your other
software, it is recommended that it be installed in its own virtual
environment.

To create a virtual environment called ``venv``, first navigate to the
location you wish to create the virtual environment in on your system,
and then run the following command:

.. code:: shell

   $ python -m venv venv

You then need to activate the virtual environment as follows:

Linux:

.. code:: shell

   $ . ./venv/bin/activate

Windows:

.. code:: shell

   $ . ./venv/Scripts/activate

Installing APDS-Pusher
~~~~~~~~~~~~~~~~~~~~~~

Now that the virtual environment is activated, you can install
``APDS-Pusher`` :

.. code:: shell

   (venv) $ python -m pip install git+https://github.com/British-Oceanographic-Data-Centre/APDS-Pusher


You can check that it is installed correctly by now running:

.. code:: shell

   (venv) $ bodc-archive-pusher --help

This should display the help for the tool (see also next section) if it
is installed correctly.

--------------

Usage instructions
------------------

The ``APDS-Pusher`` tool provides several options for usage from the
command line, and once running will periodically check for new files to
be sent to the BODC archive. The tool can be used to start the archival
process for a particular deployment-id or stop the archival for a
particular deployment-id.

In order to start the archival process to send data using the tool, you
will need the following:

1. The identifier of the deployment to which your data belongs,
2. The path to your deployment data directory, and
3. A configuration file which defines some global settings for the tool.

In order to stop the archival process you will need the following:

1. The identifier of the deployment which needs to stop archiving,
2. A configuration file which defines some global settings for the tool.

The configuration file should have the following information (although
the contents might differ depending on your particular use case) and be
saved as a ``.json`` file:

.. code:: json

   {
       "auth0_tenant": "bodc.eu.auth0.com",
       "client_id" : "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET",
       "auth2_audience": "who-am-i-talking-to",
       "bodc_archive_url" : "test_archive_url",
       "file_formats" : [".sbd", ".tbd", ".cac"],
       "archive_checker_frequency" : 100,
       "save_file_location": "/path/to/output/directory",
       "log_file_location": "/path/to/output/directory"
   }

An explanation of each field follows, if you are uncertain as to what
values they should take, contact BODC for an example file:

-  ``auth0_tenant``: This is the name of the service used to
   authenticate the tool with BODC.
-  ``client_id``: This is the name of the organisation you will send the
   data as, which is used for authentication, as provided by BODC.
-  ``client_secret``: This is the authentication secret for the
   organisation, as provided by BODC.
- ``auth2_audience``: This is the name of the application, as provided by BODC.
-  ``bodc_archive_url``: This is the URL which files will be pushed to.
-  ``file_formats``: A list of file extensions. When searching for files
   to be sent, only files with these extensions will be sent for upload.
-  ``archive_checker_frequency``: The number of minutes between attempts
   to upload new files.
-  ``save_file_location``: A path to the directory where a list of
   uploaded files will be written to disk.
-  ``log_file_location``: A path to the directory where the logs of
   ``APDS-Pusher`` will be written to disk.

Example
~~~~~~~

An example invocation of the tool is shown below:

.. code:: shell

   bodc-archive-pusher start --deployment-id 123 --data-directory /data/dep-123 --config-file /data/config.json --production --no-dry-run
   bodc-archive-pusher stop --deployment-id 123 --config-file /data/config.json

The options used above are explained below:

-  ``--deployment-id 123``: This tells the tool that the data being
   uploaded belongs to deployment ``123``.
-  ``--data-directory /data/dep-123``: This tells the tool to
   periodically scan the directory ``/data/dep-123`` for new data, and
   send it to the BODC archive.
-  ``--config-file /data/config.json``: This tells the tool that the
   configuration information is stored in the file located at
   ``/data/config.json``.
-  ``--production``: This tells the tool to upload the data to the
   production archive. Alternatively, for testing, you can use
   ``--non-production`` which will upload to the test archive. Refer to
   the `APDS-Pusher options <#command-line-options>`__ for the default
   value if this is not specified.
-  ``--no-dry-run``: This tells the tool to actually perform the file
   upload. Alternatively, if you just wish to see which files would be
   uploaded (but not actually upload them), you can use the
   ``--dry-run`` flag instead which will print the files to the
   terminal. Refer to the `APDS-Pusher
   options <#command-line-options>`__ for the default value if this is
   not specified.

Command line options
~~~~~~~~~~~~~~~~~~~~

::

   Usage: bodc-archive-pusher [OPTIONS]

     This application allows organisations to continuously push data to BODC from
     the command line.

   Options:
     --deployment-id TEXT            The Code/ID for the specific
                                     deployment.  [required]
     --data-directory DIRECTORY      Full path to the directory where
                                     files to be uploaded are stored.
                                     [required]
     --config-file FILE              Full path to config file used for
                                     authentication.  [required]
     --production / --non-production
                                     Use this flag to switch between
                                     production and non-production
                                     environments.  [default: non-
                                     production]
     --dry-run / --no-dry-run        Use this flag to switch between a
                                     regular run and a dry run send of
                                     files.  [default: no-dry-run]
     --recursive / --non-recursive   Use this flag to switch between
                                     recursive and non-recursive
                                     searching of files.  [default:
                                     recursive]
     --help                          Show this message and exit.
