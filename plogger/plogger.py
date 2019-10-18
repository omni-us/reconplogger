
import os
import yaml
import logging
import logging.config


plogger_default = {
    'version': 1,  # required
    'formatters': {
        'json': {
            'format': '%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s',
            'class': 'logmatic.jsonlogger.JsonFormatter'
        }
    },
    'handlers': {
        'json': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
    },
    'loggers': {
        'plogger': {
            'level': 'DEBUG',
            'handlers': ['json']
        }
    }
}


def load_config(cfg=None):
    """Loads a logging configuration from path or environment variable or dictionary object.

    Args:
        cfg (str or dict or None): Path to configuration file (json|yaml), or name of environment variable (json|yaml) or configuration object or None or "plogger_default" to use default configuration.
    
    Returns:
        The logging package object.
    """
    if cfg is None or cfg == 'plogger_default':
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
