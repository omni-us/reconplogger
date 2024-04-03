.. image:: https://circleci.com/gh/omni-us/reconplogger.svg?style=svg
    :target: https://circleci.com/gh/omni-us/reconplogger
.. image:: https://codecov.io/gh/omni-us/reconplogger/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/omni-us/reconplogger
.. image:: https://badge.fury.io/py/reconplogger.svg
    :target: https://badge.fury.io/py/reconplogger
.. image:: https://img.shields.io/badge/contributions-welcome-brightgreen.svg
    :target: https://github.com/omni-us/reconplogger

reconplogger - omni:us python logger
====================================

This repository contains the code of reconplogger, a python package intended to
ease the standardization of logging within omni:us. The main design decision of
reconplogger is to allow total freedom to reconfigure loggers without hard
coding anything.

The package contains essentially the following things:

- A default logging configuration.
- A function for loading logging configuration for regular python code.
- A function for loading logging configuration for flask-based microservices.
- An inheritable class to add a logger property.
- A context manager to set and get the correlation id.
- Lower level functions for:

  - Loading logging configuration from any of: config file, environment variable, or default.
  - Replacing the handlers of an existing Logger object.
  - Function to add a file handler to a logger.


How to use
==========

There are two main use cases reconplogger targets. One is for logging in regular
generic python code and the second one is logging in microservices. See the two
standardizing sections below for a detailed explanation of the two use cases.


Add as requirement
------------------

The first step to use reconplogger is adding it as a requirement in the
respective package where it will be used. This means adding it in the file
`setup.cfg` as an item in :code:`install_requires` or in an
:code:`extras_require` depending on whether reconplogger is intended to be a
core or an optional requirement.

Note: It is highly discouraged to develop packages in which requirements are
added directly to `setup.py` or to have an ambiguous `requirements.txt` file.
See the `setup.cfg` file in the reconplogger source code for reference.


Default logging configuration
-----------------------------

A feature that reconplogger provides is the possibility of externally setting
the logging configuration without having to change code or implement any parsing
of configuration. However, if a logging configuration is not given externally,
reconplogger provides a default configuration.

The default configuration defines three handlers, two of which are stream
handlers and are set to DEBUG log level. The first handler called
:code:`plain_handler` uses a simple plain text formatter, and the second handler
called :code:`json_handler` as the name suggests outputs in json format, using
the `logmatic <https://pypi.org/project/logmatic-python/>`_ JsonFormatter class.
The third handler called :code:`null_handler` is useful to disable all logging.

For each handler the default configuration defines a corresponding logger:
:code:`plain_logger`, :code:`json_logger` and :code:`null_logger`.


Standardizing logging in regular python
---------------------------------------

One objective of reconplogger is to ease the use of logging and standardize the
way it is done across all omni:us python code. The use of reconplogger comes
down to calling one function to get the logger object. For regular python code
(i.e. not a microservice) the function to use is
:func:`reconplogger.logger_setup`.

The following code snippet illustrates the use:

.. code-block:: python

    import reconplogger

    # Default plain logger
    logger = reconplogger.logger_setup()
    logger.info('My log message')

    # Json logger and custom prefix
    logger = reconplogger.logger_setup('json_logger', env_prefix='MYAPP')
    logger.info('My log message in json format')

This function gives you the ability to set the default logger to use
(:code:`logger_name` argument whose default value is :code:`plain_logger`) and
optionally provide a logging :code:`config` and/or a logging :code:`level` that
overrides the level in the config.

All of these values can be overridden via environment variables whose names are
prefixed by the value of the :code:`env_prefix` argument. The environment
variables supported are: :code:`{env_prefix}_CFG`, :code:`{env_prefix}_NAME` and
:code:`{env_prefix}_LEVEL`. Note that the environment variable names are not
required to be prefixed by the default :code:`env_prefix='LOGGER'`. The prefix
can be chosen by the user for each particular application.

For functions or classes that receive logger object as an argument, it might be
desired to set a non-logging default so that it can be called without specifying
one. For this reconplogger defines :code:`null logger` that could be used as
follows:

.. code-block:: python

    from reconplogger import null_logger

    ...

    def my_func(arg1, arg2, logger=null_logger):

    ...


Standardizing logging in flask-based microservices
--------------------------------------------------

The most important objective of reconplogger is to allow standardization of a
structured logging format for all microservices developed. Thus, the logging
from all microservices should be configured like explained here. The use is
analogous to the previous case, but using the function
:func:`reconplogger.flask_app_logger_setup` instead, and giving as first argument
the flask app object.

Additional to the previous case, this function:

- Replaces the flask app and werkzeug loggers to use a reconplogger configured one.
- Add to the logs the correlation_id
- Add before and after request functions to log the request details when the request is processed
- Patch the *requests* library forwarding the correlation id in any call to other microservices

**What is the correlation ID?**
In a system build with microservices we need a way to correlate logs coming from different microservices to the same "external" call.
For example when a user of our system do a call to the MicroserviceA this could need to retrieve some information from the MicroserviceB,
if there is an error and we want to check the logs of the MicroserviceB related to the user call we don't have a way to correlate them,
to solve this we use the correlation id!
It is a unique string that is passed in the headers of the REST calls and will be forwarded automatically when we do calls with the library *requests*. All of this is taken care in the background by this library.
If the correlation id its not present in the request headers, it will not be generated. It is up to developers to explicitly create a correlation id.


The usage would be as follows:

.. code-block:: python

    import reconplogger
    from flask import Flask

    ...

    app = Flask(__name__)

    ...

    logger = reconplogger.flask_app_logger_setup(app, level='DEBUG')

    ## NOTE: do not change logger beyond this point!

    ...

    ## Use logger in code
    myclass = MyClass(..., logger=logger)

    ...

    ## User logger in a flask request
    @app.route('/')
    def hello_world():
        logger.info('i like logs')
        correlation_id = reconplogger.get_correlation_id()
        logger.info('correlation id for this request: '+correlation_id)
        return 'Hello, World!'

    ...

As illustrated in the previous example the :func:`get_correlation_id` function
can be used to get the correlation id for the current application context.
However, there are cases in which it is desired to set the correlation id,
instead of getting a randomly generated one. In this case the
:func:`get_correlation_id` function is used, for example as follows:

.. code-block:: python

    @app.route('/')
    def hello_world():
        reconplogger.set_correlation_id('my_correlation_id')
        logger.info('i like logs')
        return 'Hello, World!'

An important note is that after configuring the logger, the code should not
modify the logger configuration. For example, the logging level should not be
modified. Adding an additional handler to the logger is not a problem. This
could be desired for example to additionally log to a file.

In the helm `values.yaml` file of the microservice, the default values for the
environment variables should be set as:

.. code-block:: yaml

    LOGGER_CFG:
    LOGGER_NAME: json_logger
    LOGGER_LEVEL: DEBUG

With the :code:`json_logger` logger, the format of the logs should look
something like the following::

    {"asctime": "2018-09-05 17:38:38,137", "levelname": "INFO", "filename": "test_formatter.py", "lineno": 5, "message": "Hello world"}
    {"asctime": "2018-09-05 17:38:38,137", "levelname": "DEBUG", "filename": "test_formatter.py", "lineno": 9, "message": "Hello world"}
    {"asctime": "2018-09-05 17:38:38,137", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 13, "message": "Hello world"}
    {"asctime": "2018-09-05 17:38:38,137", "levelname": "CRITICAL", "filename": "test_formatter.py", "lineno": 17, "message": "Hello world"}
    {"asctime": "2018-09-05 17:38:38,137", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 25, "message": "division by zero"}
    {"asctime": "2018-09-05 17:38:38,138", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 33, "message": "Exception has occured", "exc_info": "Traceback (most recent call last):\n  File \"reconplogger/tests/test_formatter.py\", line 31, in test_exception_with_trace\n    b = 100 / 0\nZeroDivisionError: division by zero"}
    {"asctime": "2018-09-05 17:38:38,138", "levelname": "INFO", "filename": "test_formatter.py", "lineno": 37, "message": "Hello world", "context check": "check"}

    {"asctime": "2020-09-02 17:20:16,428", "levelname": "INFO", "filename": "hello.py", "lineno": 12, "message": "i like logs", "correlation_id": "3958f378-5d48-4e1c-b83b-3c6d9f95faec"}
    {"asctime": "2020-09-02 17:20:16,428", "levelname": "INFO", "filename": "reconplogger.py", "lineno": 271, "message": "Request is completed", "http_endpoint": "/", "http_method": "GET", "http_response_code": 200, "http_response_size": 56, "http_input_payload_size": null, "http_input_payload_type": null, "http_response_time": "0.0002014636993408203", "correlation_id": "3958f378-5d48-4e1c-b83b-3c6d9f95faec"}


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


Adding a file handler
---------------------

In some circumstances it is desired to add to a logger a file handler so that
the logging messages are also saved to a file. This normally requires at least
three lines of code, thus to simplify things reconplogger provides the
:func:`reconplogger.add_file_handler` function to do the same with a single line
of code. The use is quite straightforward as::

    reconplogger.add_file_handler(logger, '/path/to/log/file.log')


Adding a logging property
-------------------------

When implementing classes it is common to add logging support to it. For this an
inheritable class :class:`.RLoggerProperty` is included in reconplogger to add an
:code:`rlogger` property to easily set and get the reconplogger logger. An
example of use is the following:

.. code-block:: python

    from reconplogger import RLoggerProperty

    class MyClass(RLoggerProperty):
        def __init__(self, logger):
            self.rlogger = logger
        def my_method(self):
            self.rlogger.error('my_method was called')

    MyClass(logger=True).my_method()


Overriding logging configuration
--------------------------------

An important feature of reconplogger is that the logging configuration of apps
that use it can be easily changed via the environment variables. First set the
environment variables with the desired logging configuration and logger name:

.. code-block:: bash

    export LOGGER_NAME="example_logger"

    export LOGGER_CFG='{
        "version": 1,
        "formatters": {
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
            }
        },
        "handlers": {
            "console":{
                "level":"DEBUG",
                "class":"logging.StreamHandler",
                "formatter": "verbose"
            }
        },
        "loggers": {
            "example_logger": {
                "handlers": ["console"],
                "level": "ERROR",
            }
        }
    }'

Then, in the python code the logger would be used as follows:

.. code-block:: python

    >>> import reconplogger
    >>> logger = reconplogger.logger_setup(env_prefix='LOGGER')
    >>> logger.error('My error message')
    ERROR 2019-10-18 14:45:22,629 <stdin> 16876 139918773925696 My error message


Low level functions
===================


Loading configuration
---------------------

The :func:`reconplogger.load_config` function allows loading of a python logging
configuration. The format config can be either json or yaml. The loading of
configuration can be from a file (giving its path), from an environment variable
(giving the variable name), a raw configuration string, or loading the default
configuration that comes with reconplogger. See below examples of loading for
each of the cases:

.. code-block:: python

    import reconplogger

    ## Load from config file
    reconplogger.load_config('/path/to/config.yaml')

    ## Load from environment variable
    reconplogger.load_config('LOGGER_CFG')

    ## Load default config
    reconplogger.load_config('reconplogger_default_cfg')


Replacing logger handlers
-------------------------

In some cases it might be needed to replace the handlers of some already
existing logger. For this reconplogger provides the
:func:`reconplogger.replace_logger_handlers` function. To use it, simply provide
the logger in which to replace the handlers and the logger from where to get the
handlers. The procedure would be as follows:

.. code-block:: python

    import reconplogger

    logger = reconplogger.logger_setup('json_logger')
    reconplogger.replace_logger_handlers('some_logger_name', logger)


Contributing
============

Contributions to this package are very welcome. When you plan to work with the
source code, note that this project does not include a `requirements.txt` file.
This is by intention. To make it very clear what are the requirements for
different use cases, all the requirements of the project are stored in the file
`setup.cfg`. The basic runtime requirements are defined in section
:code:`[options]` in the :code:`install_requires` entry. All optional
requirements are stored in section :code:`[options.extras_require]`. There are
:code:`test`, :code:`dev` and :code:`doc` extras require to be used by
developers (e.g. requirements to run the unit tests) and an :code:`all` extras
require for optional runtime requirements, namely Flask support.

The recommended way to work with the source code is the following. First clone
the repository, then create a virtual environment, activate it and finally
install the development requirements. More precisely the steps would be:

.. code-block:: bash

    git clone https://github.com/omni-us/reconplogger.git
    cd reconplogger
    virtualenv -p python3 venv
    . venv/bin/activate

The crucial step is installing the requirements which would be done by running:

.. code-block:: bash

    pip3 install --editable ".[dev]"

Running the unit tests can be done either using using `tox
<https://tox.readthedocs.io/en/stable/>`__ or the :code:`setup.py` script. The
unit tests are also installed with the package, thus can be used to in a
production system.

.. code-block:: bash

    tox  # Run tests using tox
    ./setup.py test_coverage  # Run tests and generate coverage report
    python3 -m reconplogger_tests  # Run tests for installed package


Pull requests
-------------

- To contribute it is required to create and push to a new branch and issue a
  pull request.

- A pull request will only be accepted if:

    - All python files pass pylint checks.
    - All unit tests run successfully.
    - New code has docstrings and gets included in the html documentation.

- When developing, after cloning be sure to run the githook-pre-commit to setup
  the pre-commit hook. This will help you by automatically running pylint before
  every commit.

Using bump version
------------------

Only the maintainer of this repo should bump versions and this should be done
only on the master branch. To bump the version it is required to use the
bumpversion command that should already be installed if :code:`pip3 install
--editable .[dev,doc,test,all]` was run as previously instructed.

.. code-block:: bash

    bumpversion major/minor/patch

Push the tags to the repository as well.

.. code-block:: bash

    git push; git push --tags

When the version tags are pushed, circleci will automatically build the wheel
file, test it and if successful, push the package to pypi.
