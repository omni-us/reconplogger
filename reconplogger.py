
import os
import yaml
import logging
import logging.config


__version__ = '3.1.0'


reconplogger_format = '%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s'

reconplogger_default = {
    'version': 1,
    'formatters': {
        'plain': {
            'format': reconplogger_format,
        },
        'json': {
            'format': reconplogger_format,
            'class': 'logmatic.jsonlogger.JsonFormatter'
        },
    },
    'handlers': {
        'plain_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'plain',
        },
        'json_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'null_handler': {
            'class': 'logging.NullHandler',
        }
    },
    'loggers': {
        'plain_logger': {
            'level': 'DEBUG',
            'handlers': ['plain_handler'],
        },
        'json_logger': {
            'level': 'DEBUG',
            'handlers': ['json_handler'],
        },
        'null_logger': {
            'handlers': ['null_handler'],
        },
    },
}


null_logger = logging.Logger('null')
null_logger.addHandler(logging.NullHandler())


def load_config(cfg=None):
    """Loads a logging configuration from path or environment variable or dictionary object.

    Args:
        cfg (str or dict or None): Path to configuration file (json|yaml), or name of environment variable (json|yaml) or configuration object or None/"reconplogger_default" to use default configuration.

    Returns:
        The logging package object.
    """
    if cfg is None or cfg == 'reconplogger_default' or (cfg in os.environ and os.environ[cfg] == 'reconplogger_format'):
        cfg_dict = reconplogger_default
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
            raise ValueError(
                'Received string which is neither a path to an existing file or the name of an set environment variable :: '+str(ex))

    logging.config.dictConfig(cfg_dict)
    # To prevent double logging if root logger is used
    logging.root.handlers = [logging.NullHandler()]

    return logging


def replace_logger_handlers(logger, handlers='reconplogger'):
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
            raise ValueError(
                'Expected handlers list to include only StreamHandler objects.')
    elif isinstance(handlers, str):
        if handlers not in logging.root.manager.loggerDict:
            raise ValueError('Logger "'+handlers+'" not defined.')
        handlers = logging.getLogger(handlers).handlers
    elif isinstance(logger, logging.Logger):
        handlers = handlers.handlers
    else:
        raise ValueError(
            'Expected handlers to be list, logger name or Logger object.')

    ## Replace handlers ##
    logger.handlers = list(handlers)


def add_file_handler(logger, file_path, format=reconplogger_format, level=logging.DEBUG):
    """Adds a file handler to a given logger.

    Args:
        logger (logging.Logger): Logger object where to add the file handler.
        file_path (str): Path to log file for handler.
        format (str): Format for logging.
        level (int): Logging level for the handler.
    """
    fileHandler = logging.FileHandler(file_path)
    fileHandler.setFormatter(logging.Formatter(format))
    fileHandler.setLevel(level)
    logger.addHandler(fileHandler)


def test_logger(logger):
    """Logs one message to each debug, info and warning levels intended for testing."""
    logger.debug('reconplogger test debug message.')
    logger.info('reconplogger test info message.')
    logger.warning('reconplogger test warning message.')


def logger_setup(env_cfg=None, env_name=None, init_messages=False):
    """Sets up logging configuration and returns the logger.

    If env_cfg is unset, the default reconplogger config is used. If env_name is
    unset, 'plain_logger' logger is used.

    Args:
        env_cfg (str): Name of environment variable containing the logging configuration.
        env_name (str): Name of environment variable containing the logger to use.
        init_messages (bool): Whether to log init and test messages.

    Returns:
        logging.Logger: The logger object.
    """

    ## Configure logging ##
    load_config(None if env_cfg is None else os.getenv(env_cfg))

    ## Get logger ##
    logger_name = 'plain_logger'
    if isinstance(env_name, str) and env_name in os.environ:
        logger_name = os.getenv(env_name)
    if logger_name not in logging.Logger.manager.loggerDict:
        raise ValueError('Logger "'+logger_name+'" not defined.')
    logger = logging.getLogger(logger_name)

    ## Log configured done and test logger ##
    if init_messages:
        logger.info('reconplogger (v'+__version__+') logger configured.')
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

    # Configure logging and get logger ##
    logger = logger_setup(env_cfg, env_name)

    # Replace flask logger ##
    flask_app.logger = logger

    # Replace werkzeug logger handlers ##
    replace_logger_handlers('werkzeug', os.getenv(
        env_name, 'plain_logger'))

    return logger
