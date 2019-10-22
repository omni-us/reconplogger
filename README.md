plogger - omni:us python logger
===============================

This repository contains the code of plogger, a python package to ease the
standardization of logging within omni:us. The main design decision of plogger
is to allow total freedom to reconfigure loggers without hard coding anything.

The package contains essentially three things:

- A default logging configuration.
- A function to load logging configuration from any of: config file, environment variable, or default.
- A function to replace the handlers of an existing Logger object.


How to use
==========


Add as requirement
------------------

The first step to use plogger is adding it as a requirement in the respective
package where it will be used. This means adding it in the file `setup.cfg` as
an item in `install_requires` or in an `extras_require` depending on whether
plogger is intended to be a core or an optional requirement.

Note: It is highly discouraged develop packages in which requirements are added
directly to `setup.py` or to have an ambiguous `requirements.txt` file.


Loading configuration
---------------------

The most important functionality that plogger provides is the func:`load_config`
function, whose purpose is just to ease loading of a python logging
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


Using a configured logger
-------------------------

After loading a logging configuration, using a logger is as usual with the
python logging library. Just get the respective logger and use it. The only
thing to consider is that to allow total freedom to reconfigure loggers without
hard coding anything, the name of the logger should also be a variable. So,
a logging configuration might define many handlers and loggers, whose names
are unknown to the program using plogger. So the name of the logger to use
should also be given as parameter.

Consider for example that you have an environment variable with the name of the
logger to use that is defined in a logging configuration defined in another
environment variable, as follows:

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

    >>> import os
    >>> import plogger

    >>> logging = plogger.load_config('PLOGGER_CFG')
    >>> logger = logging.getLogger(os.environ['PLOGGER_NAME'])

    >>> logger.error('My error message')
    ERROR 2019-10-18 14:45:22,629 <stdin> 16876 139918773925696 My error message


Replacing logger handlers
-------------------------

In some cases it might be needed to replace the handlers of some already
existing logger. For this plogger provides the :func:`replace_logger_handlers`
function. To use it, simply provide the logger in which to replace the handlers
and the logger from where to get the handlers. Using the same environment
variables as above, the procedure would be as follows:

.. code-block:: python

    import plogger

    plogger.load_config('PLOGGER_CFG')
    plogger.replace_logger_handlers('some_logger_name', os.environ['PLOGGER_NAME'])


Standardizing logging in flask-based microservices
==================================================

The most important objective of plogger is to allow standardization logging from
all microservices developed. Thus, the logging from all microservices should be
configured like explained here. All important sources of logs should be
reconfigured, so that all logs have a common format and can be properly indexed.

.. code-block:: python

    import plogger
    from flask import Flask

    ...

    app = Flask(__name__)

    ...

    logger = plogger.flask_app_logger_setup('PLOGGER_CFG', 'PLOGGER_NAME', app)

    ## NOTE: do not change logger beyond this point!

    ...

    ## Use
    myclass = MyClass(..., logger=logger)

    ...

An important note is that after configuring the logger, the code should not
modify the logger configuration. For example, do not set the logging level.

In the helm `values.yaml` of the microservice, the default values for the
envirnoment variables should be set as:

.. code-block:: yaml

    PLOGGER_CFG: plogger_default
    PLOGGER_NAME: plogger


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
