plogger - omni:us python logger
===============================

This repository contains the code of plogger, a python package to ease the
standardization of logging within omni:us. The main design decision of plogger
is to allow total freedom to reconfigure loggers without hard coding anything.

The package contains essentially three things:

- A default logging configuration.
- A function for loading logging configuration for regular python code.
- A function for loading logging configuration for flask-based microservices.
- Lower level functions for:

  - Loading logging configuration from any of: config file, environment variable, or default.
  - Replacing the handlers of an existing Logger object.


How to use
==========

There are two main use cases plogger targets. One is for logging in regular
generic python code and the second one is logging in microservices. See the two
standardizing sections below for a detailed explanation of the two use cases.


Add as requirement
------------------

The first step to use plogger is adding it as a requirement in the respective
package where it will be used. This means adding it in the file `setup.cfg` as
an item in `install_requires` or in an `extras_require` depending on whether
plogger is intended to be a core or an optional requirement.

Note: It is highly discouraged to develop packages in which requirements are
added directly to `setup.py` or to have an ambiguous `requirements.txt` file.
See the `setup.cfg` file in the plogger source code for reference.


Default logging configuration
-----------------------------

An feature that plogger provides is the possibility of externally setting the
logging configuration without having to change code or implement any parsing of
configuration. However, if a logging configuration is not given externally,
plogger provide a default configuration.

The default configuration defines two handlers, both of which are stream
handlers and are set to DEBUG log level. The first handler called `plain` uses a
simple plain text formatter, and the second handler called `json` as the name
suggests outputs in json format using the `logmatic
<https://pypi.org/project/logmatic-python/>`_ JsonFormatter class.

For each handler the default configuration defines a corresponding logger:
:code:`plogger_plain` and :code:`plogger_json`.


Standardizing logging in regular python
---------------------------------------

One objective of plogger is to ease the use of logging and standardize the way
it is done across all omni:us python code. The use of plogger comes down to
calling one function to get the logger object. For regular python code (i.e. not
a microservice) the function to use is :func:`plogger.logger_setup`. To this
function you give as argument two strings, which are names of environment
variables, one for the logging configuration and the other for the name of the
logger to use. The following code snippet illustrates the use:

.. code-block:: python

    import plogger

    ...

    logger = plogger.logger_setup('PLOGGER_CFG', 'PLOGGER_NAME')

    ...

    logger.info('My log message')

If the environment variables are not set, this function returns the
:code:`plogger_plain` logger from the default configuration.


Standardizing logging in flask-based microservices
--------------------------------------------------

The most important objective of plogger is to allow standardization of a
structured logging format for all microservices developed. Thus, the logging
from all microservices should be configured like explained here. The use is
analogous to the previous case, but using the
:func:`plogger.flask_app_logger_setup` instead, and giving as a third argument
the flask app object. Additional to the previous case, this function replaces
the flask app and werkzeug loggers to use a plogger configured one. The usage
would be as follows:

.. code-block:: python

    import plogger
    from flask import Flask

    ...

    app = Flask(__name__)

    ...

    logger = plogger.flask_app_logger_setup('PLOGGER_CFG', 'PLOGGER_NAME', app)

    ## NOTE: do not change logger beyond this point!

    ...

    ## Use logger in code
    myclass = MyClass(..., logger=logger)

    ...

An important note is that after configuring the logger, the code should not
modify the logger configuration. For example, the logging level should not be
modified, or only modified by providing a non-default option. Adding an
additional handler to the logger is not a problem. This could be desired for
example to also log to a file.

In the helm `values.yaml` file of the microservice, the default values for the
environment variables should be set as:

.. code-block:: yaml

    PLOGGER_CFG: plogger_default
    PLOGGER_NAME: plogger_json

With the :code:`plogger_json` logger, the format of the logs should look
something like the following::

    {"asctime": "2018-09-05 17:38:38,137", "levelname": "INFO", "filename": "test_formatter.py", "lineno": 5, "message": "Hello world"}
    {"asctime": "2018-09-05 17:38:38,137", "levelname": "DEBUG", "filename": "test_formatter.py", "lineno": 9, "message": "Hello world"}
    {"asctime": "2018-09-05 17:38:38,137", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 13, "message": "Hello world"}
    {"asctime": "2018-09-05 17:38:38,137", "levelname": "CRITICAL", "filename": "test_formatter.py", "lineno": 17, "message": "Hello world"}
    {"asctime": "2018-09-05 17:38:38,137", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 25, "message": "division by zero"}
    {"asctime": "2018-09-05 17:38:38,138", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 33, "message": "Exception has occured", "exc_info": "Traceback (most recent call last):\n  File \"plogger/tests/test_formatter.py\", line 31, in test_exception_with_trace\n    b = 100 / 0\nZeroDivisionError: division by zero"}
    {"asctime": "2018-09-05 17:38:38,138", "levelname": "INFO", "filename": "test_formatter.py", "lineno": 37, "message": "Hello world", "context check": "check"}


Use of the logger object
------------------------

The logger objects returned by the setup functions are normal python
:code:`logging.Logger` objects, so all the standard logging functionalities
should be used. Please refer to the `logging package documentation
<https://docs.python.org/3/howto/logging.html>`_ for details.

A couple of logging features that should be very commonly used are the
following. To add additional structured information to a log, the :code:`extra`
argument should be used. A simple example could be::

    logger.info('Successfully processed document', extra={'uuid': uuid})

When an exception occurs the :code:`exc_info=True` argument should be used, for
example::

    try:
        ...
    except:
        logger.critical('Failed to run task', exc_info=True)


Overriding logging configuration
--------------------------------

An important feature of plogger is that the logging configuration of apps that
use it can be easily changed via the environment variables given to the logger
setup functions. Using the same environment variables as the previous examples,
the following could be done. First set the environment variables with the
desired logging configuration and logger name:

.. code-block:: bash

    export PLOGGER_NAME="example_logger"

    export PLOGGER_CFG="{
        'version': 1,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
        },
        'handlers': {
            'console':{
                'level':'DEBUG',
                'class':'logging.StreamHandler',
                'formatter': 'verbose'
            },
        },
        'loggers': {
            'example_logger': {
                'handlers': ['console'],
                'level': 'ERROR',
            },
        }
    }"

Then, in the python code the logger would be used as follows:

.. code-block:: python

    >>> import plogger
    >>> logger = plogger.logger_setup('PLOGGER_CFG', 'PLOGGER_NAME')
    >>> logger.error('My error message')
    ERROR 2019-10-18 14:45:22,629 <stdin> 16876 139918773925696 My error message


Low level functions
===================


Loading configuration
---------------------

The :func:`plogger.load_config` function allows loading of a python logging
configuration. The loading of configuration can be from a file (giving its
path), from an environment variable (giving the variable name), or loading the
default configuration that comes with plogger. The loading from file and from
environment variable expects the format to be yaml or json. See below examples
of loading for each of the cases:

.. code-block:: python

    import plogger

    ## Load from config file
    plogger.load_config('/path/to/config.yaml')

    ## Load from environment variable
    plogger.load_config('PLOGGER_CFG')

    ## Load default config
    plogger.load_config('plogger_default')


Replacing logger handlers
-------------------------

In some cases it might be needed to replace the handlers of some already
existing logger. For this plogger provides the
:func:`plogger.replace_logger_handlers` function. To use it, simply provide the
logger in which to replace the handlers and the logger from where to get the
handlers. Using the same environment variables as above, the procedure would be
as follows:

.. code-block:: python

    import plogger

    plogger.load_config('PLOGGER_CFG')
    plogger.replace_logger_handlers('some_logger_name', os.environ['PLOGGER_NAME'])


Contributing
============

Contributions to this package are very welcome. When you intend to work with the
source code, note that this project does not include a :code:`requirements.txt`
file. This is by intention. To make it very clear what are the requirements for
different use cases, all the requirements of the project are stored in the file
:code:`setup.cfg`. The basic runtime requirements are defined in section
:code:`[options]` in the :code:`install_requires` entry. All optional
requirements are stored in section :code:`[options.extras_require]`. There is a
:code:`dev` extras require to be used by developers (e.g. requirements to run
the unit tests) and a :code:`bump` extras require for the maintainer of the
package.

The recommended way to work with the source code is the following. First clone
the repository, then create a virtual environment, activate it and finally
install the development requirements. More precisely the steps would be:

.. code-block:: bash

    git clone ssh://git@code.omnius.corp:7999/bkd/plogger.git
    cd plogger
    virtualenv -p python3 venv
    . venv/bin/activate

The crucial step is installing the requirements which would be done by running:

.. code-block:: bash

    pip3 install --editable .[dev]

After changing the code, always run unit tests as follows:

.. code-block:: bash

    ./setup.py test


Pull requests
-------------

- The master branch in bitbucket is blocked for pushing. Thus to contribute it
  is required to create and push to a new branch and issue a pull request.

- A pull request will only be accepted if:

    - All python files pass pylint checks.
    - All unit tests run successfully.
    - New code has docstrings and gets included in the html documentation.

- When developing, after cloning be sure to run the githook-pre-commit to setup
  the pre-commit hook. This will help you by automatically running pylint before
  every commit.


Using bump version
------------------

As part of contribution please use bumpversion to bump up the version on master.

.. code-block:: bash

    bumpversion major/minor/path

Push the tags to the repository as well 

.. code-block:: bash

    git push; git push --tags

Create the wheel file and push to pypi repository using twine

.. code-block:: bash

    ./setup.py bdist_wheel
    twine upload --repository-url https://pypi.omnius.com --username jenkins --password "" dist/plogger-<version>-py3-none-any.whl
