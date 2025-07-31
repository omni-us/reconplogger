.. image:: https://readthedocs.org/projects/reconplogger/badge/?version=stable
    :target: https://readthedocs.org/projects/reconplogger/
.. image:: https://codecov.io/gh/omni-us/reconplogger/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/omni-us/reconplogger
.. image:: https://badge.fury.io/py/reconplogger.svg
    :target: https://badge.fury.io/py/reconplogger
.. image:: https://img.shields.io/badge/contributions-welcome-brightgreen.svg
    :target: https://github.com/omni-us/reconplogger

reconplogger - omni:us python logger
====================================

Docs: https://reconplogger.readthedocs.io/ | Source: https://github.com/omni-us/reconplogger/

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
