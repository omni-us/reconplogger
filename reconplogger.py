
import os
import yaml
import logging
import logging.config
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
import uuid
import sys
import time


__version__ = '4.3.1'


try:
    # If flask is installed import the request context objects
    from flask import request, g, has_request_context
    # If requests is installed patch the calls to add the correlation id
    import requests
    def _request_patch(slf, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        if has_request_context():
            headers["Correlation-ID"] = g.correlation_id
        return slf.request_orig(*args, **kwargs, headers=headers)
    setattr(requests.sessions.Session, 'request_orig', requests.sessions.Session.request)
    requests.sessions.Session.request = _request_patch
except:
    pass

reconplogger_format = '%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s'

reconplogger_default_cfg = {
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
            'level': 'WARNING',
        },
        'json_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'level': 'WARNING',
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

logging_levels = {
    'CRITICAL': CRITICAL,
    'ERROR':    ERROR,
    'WARNING':  WARNING,
    'INFO':     INFO,
    'DEBUG':    DEBUG,
    'NOTSET':   NOTSET,
}
logging_levels.update({v: v for v in logging_levels})

null_logger = logging.Logger('null')
null_logger.addHandler(logging.NullHandler())


def load_config(cfg=None):
    """Loads a logging configuration from path or environment variable or dictionary object.

    Args:
        cfg (str or dict or None): Path to configuration file (json|yaml), or name of environment variable (json|yaml) or configuration object or None/"reconplogger_default_cfg" to use default configuration.

    Returns:
        The logging package object.
    """
    if cfg is None or cfg in {'', 'reconplogger_default_cfg'} or (cfg in os.environ and os.environ[cfg] == 'reconplogger_default_cfg'):
        cfg_dict = reconplogger_default_cfg
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
                try:
                    cfg_dict = yaml.safe_load(cfg)
                    if not isinstance(cfg_dict, dict):
                        raise ValueError
                except Exception:
                    raise ValueError
        except Exception:
            raise ValueError(
                'Received string which is neither a path to an existing file nor the name of an set environment variable nor a python dictionary string that can be consumed by logging.config.dictConfig.')

    cfg_dict['disable_existing_loggers'] = False
    logging.config.dictConfig(cfg_dict)
    # To prevent double logging if root logger is used
    logging.root.handlers = [logging.NullHandler()]

    return logging


def replace_logger_handlers(logger, handlers='plain_logger'):
    """Replaces the handlers of a given logger.

    Args:
        logger (logging.Logger or str): Object or name of logger to replace handlers.
        handlers (list[logging.StreamHandler] or logging.Logger or str): List of handlers or object or name of logger from which to get handlers.
    """
    # Resolve logger
    if isinstance(logger, str):
        logger = get_logger(logger)
    if not isinstance(logger, logging.Logger):
        raise ValueError('Expected logger to be logger name or Logger object.')

    # Resolve handlers
    if isinstance(handlers, list):
        if not all(isinstance(x, logging.StreamHandler) for x in handlers):
            raise ValueError(
                'Expected handlers list to include only StreamHandler objects.')
    elif isinstance(handlers, str):
        handlers = get_logger(handlers).handlers
    elif isinstance(logger, logging.Logger):
        handlers = handlers.handlers
    else:
        raise ValueError(
            'Expected handlers to be list, logger name or Logger object.')

    ## Replace handlers ##
    logger.handlers = list(handlers)


def add_file_handler(logger, file_path, format=reconplogger_format, level='DEBUG'):
    """Adds a file handler to a given logger.

    Args:
        logger (logging.Logger): Logger object where to add the file handler.
        file_path (str): Path to log file for handler.
        format (str): Format for logging.
        level (str or int or None): Logging level for the handler.
    """
    fileHandler = logging.FileHandler(file_path)
    fileHandler.setFormatter(logging.Formatter(format))
    if level is not None:
        if level not in logging_levels:
            raise ValueError('Invalid logging level: "'+str(level)+'".')
        fileHandler.setLevel(logging_levels[level])
    logger.addHandler(fileHandler)


def test_logger(logger):
    """Logs one message to each debug, info and warning levels intended for testing."""
    logger.debug('reconplogger test debug message.')
    logger.info('reconplogger test info message.')
    logger.warning('reconplogger test warning message.')


def get_logger(logger_name):
    """Returns an already existing logger.

    Args:
        logger_name (str):  Name of the logger to get.

    Returns:
        logging.Logger: The logger object.

    Raises:
        ValueError: If the logger does not exist.
    """
    if logger_name not in logging.Logger.manager.loggerDict and logger_name not in logging.root.manager.loggerDict:
        raise ValueError('Logger "'+str(logger_name)+'" not defined.')
    return logging.getLogger(logger_name)


def logger_setup(logger_name='plain_logger', config=None, level=None, env_prefix='LOGGER', init_messages=False):
    """Sets up logging configuration and returns the logger.

    Args:
        logger_name (str):  Name of the logger that needs to be used.
        config (str or None): Configuration string or path to configuration file or configuration file via environment variable.
        level (str or int or None): Optional logging level that overrides one in config.
        env_prefix (str): Environment variable names prefix for overriding logger configuration.
        init_messages (bool): Whether to log init and test messages.

    Returns:
        logging.Logger: The logger object.
    """
    if not isinstance(env_prefix, str) or not env_prefix:
        raise ValueError('env_prefix is required to be a non-empty string.')
    env_cfg = env_prefix + '_CFG'
    env_name = env_prefix + '_NAME'
    env_level = env_prefix + '_LEVEL'

    # Configure logging
    load_config(os.getenv(env_cfg, config))

    # Get logger
    logger = get_logger(os.getenv(env_name, logger_name))

    # Override log level if set
    if env_level in os.environ:
        level = os.getenv(env_level)
    if level:
        if isinstance(level, str):
            if level not in logging_levels:
                raise ValueError('Invalid logging level: "'+str(level)+'".')
            level = logging_levels[level]
        else:
            raise ValueError('Expected level argument to be a string.')
        for handler in logger.handlers:
            handler.setLevel(level)

    # Log configured done and test logger
    if init_messages:
        logger.info('reconplogger (v'+__version__+') logger configured.')
        test_logger(logger)

    return logger


def flask_app_logger_setup(flask_app, logger_name='plain_logger', config=None, level=None, env_prefix='LOGGER'):
    """Sets up logging configuration, configures flask to use it, and returns the logger.

    Args:
        flask_app (flask.app.Flask): The flask app object.
        logger_name (str):  Name of the logger that needs to be used.
        config (str): Configuration string or path to configuration file or configuration file via environment variable.
        level (str): Optional logging level that overrides one in config.
        env_prefix (str): Environment variable names prefix for overriding logger configuration.

    Returns:
        logging.Logger: The logger object.
    """
    # Configure logging and get logger
    logger = logger_setup(logger_name=logger_name, config=config, level=level, env_prefix=env_prefix)

    # Add flask before and after request functions to augment the logs
    def _flask_logging_before_request():
        g.correlation_id = request.headers.get("Correlation-ID", str(uuid.uuid4()))
        g.start_time = time.time()
    flask_app.before_request_funcs.setdefault(None, []).append(_flask_logging_before_request)

    def _flask_logging_after_request(response):
        response.headers.set("Correlation-ID", g.correlation_id)
        logger.info("Request is completed", extra={
            "http_endpoint": request.path,
            "http_method": request.method,
            "http_response_code": response.status_code,
            "http_response_size": sys.getsizeof(response),
            "http_input_payload_size": request.content_length,
            "http_input_payload_type": request.content_type,
            "http_response_time": str(time.time() - g.start_time),
        })
        return response
    flask_app.after_request_funcs.setdefault(None, []).append(_flask_logging_after_request)

    # Add logging filter to augment the logs
    class FlaskLoggingFilter(logging.Filter):
        def filter(self, record):
            if has_request_context():
                record.correlation_id = g.correlation_id
            return True
    logger.addFilter(FlaskLoggingFilter())

    # Replace flask logger
    flask_app.logger = logger

    # Setup werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    replace_logger_handlers(werkzeug_logger, logger)
    werkzeug_logger.level = WARNING

    return logger
