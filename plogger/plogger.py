
import os
import yaml
import logging
import logging.config
from .__version__ import __version__


plogger_default = {
    'version': 1,
    'formatters': {
        'plain': {
            'format': '%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s',
        },
        'json': {
            'format': '%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s',
            'class': 'logmatic.jsonlogger.JsonFormatter'
        },
    },
    'handlers': {
        'plain': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'plain',
        },
        'json': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        'plogger_plain': {
            'handlers': ['plain'],
        },
        'plogger_json': {
            'handlers': ['json'],
        },
        'plogger': {
            'handlers': ['json'],
        },
    },
}


def load_config(cfg=None):
    """Loads a logging configuration from path or environment variable or dictionary object.

    Args:
        cfg (str or dict or None): Path to configuration file (json|yaml), or name of environment variable (json|yaml) or configuration object or None or "plogger_default" to use default configuration.
    
    Returns:
        The logging package object.
    """
    if cfg is None or cfg == 'plogger_default' or (cfg in os.environ and os.environ[cfg] == 'plogger_default'):
        cfg_dict = plogger_default
    elif isinstance(cfg, dict):
        cfg_dict = cfg
    elif isinstance(cfg, str):
        try:
            if os.path.isfile(cfg):
                with open(cfg, 'r') as f:
                    cfg_dict = yaml.safe_load(f.read())
            elif cfg in os.environ:
                cfg_dict = yaml.safe_load(os.environ[cfg])
            else:
                raise ValueError
        except Exception as ex:
            raise ValueError('Received string which is neither a path to an existing file or the name of an set environment variable :: '+str(ex))

    logging.config.dictConfig(cfg_dict)

    return logging


def replace_logger_handlers(logger, handlers='plogger'):
    """Replaces the handlers of a given logger.

    Args:
        logger (logging.Logger or str): Object or name of logger to replace handlers.
        handlers (list[logging.StreamHandler] or logging.Logger or str): List of handlers or object or name of logger from which to get handlers.
    """
    ## Resolve logger ##
    if isinstance(logger, str):
        logger = logging.getLogger(logger)
    if not isinstance(logger, logging.Logger):
        raise ValueError('Expected logger to be logger name or Logger object.')

    ## Resolve handlers ##
    if isinstance(handlers, list):
        if not all(isinstance(x, logging.StreamHandler) for x in handlers):
            raise ValueError('Expected handlers list to include only StreamHandler objects.')
    elif isinstance(handlers, str):
        if handlers not in logging.root.manager.loggerDict:
            raise ValueError('Logger "'+handlers+'" not defined.')
        handlers = logging.getLogger(handlers).handlers
    elif isinstance(logger, logging.Logger):
        handlers = handlers.handlers
    else:
        raise ValueError('Expected handlers to be list, logger name or Logger object.')

    ## Replace handlers ##
    logger.handlers = list(handlers)


def test_logger(logger):
    """Logs one message to each debug, info and warning levels intended for testing."""
    logger.debug('plogger test debug message.')
    logger.info('plogger test info message.')
    logger.warning('plogger test warning message.')


def logger_setup(env_cfg=None, env_name=None):
    """Sets up logging configuration and returns the logger.

    If env_cfg is unset, the default plogger config is used. If env_name is
    unset, 'plogger_plain' logger is used.

    Args:
        env_cfg (str): Name of environment variable containing the logging configuration.
        env_name (str): Name of environment variable containing the logger to use.

    Returns:
        logging.Logger: The logger object.
    """

    ## Configure logging ##
    load_config(None if env_cfg is None else os.getenv(env_cfg))

    ## Get logger ##
    logger = logging.getLogger(os.getenv(env_name) if env_name in os.environ else 'plogger_plain')

    ## Log configured done and test logger ##
    logger.info('plogger (v'+__version__+') logger configured.')
    test_logger(logger)

    return logger


def flask_app_logger_setup(env_cfg, env_name, flask_app):
    """Sets up logging configuration, configures flask to use it, and returns the logger.

    Args:
        env_cfg (str): Name of environment variable containing the logging configuration.
        env_name (str): Name of environment variable containing the logger to use.
        flask_app (flask.app.Flask): The flask app object.

    Returns:
        logging.Logger: The logger object.
    """

    ## Configure logging and get logger ##
    logger = logger_setup(env_cfg, env_name)

    ## Replace flask logger ##
    flask_app.logger = logger

    ## Replace werkzeug logger handlers ##
    replace_logger_handlers('werkzeug', os.getenv(env_name, 'plogger_plain'))

    return logger
