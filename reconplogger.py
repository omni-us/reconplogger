import os
import yaml
import logging
import logging.config
from contextlib import contextmanager
from contextvars import ContextVar
from importlib.util import find_spec
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
from typing import Optional, Union
import time


__version__ = "4.16.1"


try:
    # If flask is installed import the request context objects
    from flask import request, g, has_request_context

    # If requests is installed patch the calls to add the correlation id
    import requests

    def _request_patch(slf, *args, **kwargs):
        headers = kwargs.pop("headers", {})
        if has_request_context() and g.correlation_id:
            headers["Correlation-ID"] = g.correlation_id
        elif current_correlation_id.get() is not None:
            headers["Correlation-ID"] = current_correlation_id.get()
        return slf.request_orig(*args, **kwargs, headers=headers)

    setattr(
        requests.sessions.Session, "request_orig", requests.sessions.Session.request
    )
    requests.sessions.Session.request = _request_patch
except ImportError:  # pragma: no cover
    pass

reconplogger_format = (
    "%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s"
)

reconplogger_default_cfg = {
    "version": 1,
    "formatters": {
        "plain": {
            "format": reconplogger_format,
        },
        "json": {
            "format": reconplogger_format.replace("asctime", "timestamp"),
            "class": "logmatic.JsonFormatter",
        },
    },
    "handlers": {
        "plain_handler": {
            "class": "logging.StreamHandler",
            "formatter": "plain",
            "level": "WARNING",
        },
        "json_handler": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "WARNING",
        },
        "null_handler": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "plain_logger": {
            "level": "DEBUG",
            "handlers": ["plain_handler"],
        },
        "json_logger": {
            "level": "DEBUG",
            "handlers": ["json_handler"],
        },
        "null_logger": {
            "handlers": ["null_handler"],
        },
    },
}

logging_levels = {
    "CRITICAL": CRITICAL,
    "ERROR": ERROR,
    "WARNING": WARNING,
    "INFO": INFO,
    "DEBUG": DEBUG,
    "NOTSET": NOTSET,
}
logging_levels.update({v: v for v in logging_levels.values()})  # Also accept int keys

null_logger = logging.Logger("null")
null_logger.addHandler(logging.NullHandler())

configs_loaded = set()


def load_config(cfg: Optional[Union[str, dict]] = None, reload: bool = False):
    """Loads a logging configuration from path or environment variable or dictionary object.

    Args:
        cfg: Path to configuration file (json|yaml), or name of environment variable (json|yaml) or configuration object or None/"reconplogger_default_cfg" to use default configuration.

    Returns:
        The logging package object.
    """
    if (
        cfg is None
        or cfg in {"", "reconplogger_default_cfg"}
        or (cfg in os.environ and os.environ[cfg] == "reconplogger_default_cfg")
    ):
        cfg_dict = reconplogger_default_cfg
    elif isinstance(cfg, dict):
        cfg_dict = cfg
    elif isinstance(cfg, str):
        try:
            if os.path.isfile(cfg):
                with open(cfg, "r") as f:
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
                "Received string which is neither a path to an existing file nor the name of an set environment variable nor a python dictionary string that can be consumed by logging.config.dictConfig."
            )

    cfg_dict["disable_existing_loggers"] = False

    cfg_hash = yaml.safe_dump(cfg_dict).__hash__()
    if reload or cfg_hash not in configs_loaded:
        logging.config.dictConfig(cfg_dict)
        configs_loaded.add(cfg_hash)

    return logging


def replace_logger_handlers(
    logger: Union[logging.Logger, str],
    handlers: Union[logging.Logger, str],
):
    """Replaces the handlers of a given logger.

    Args:
        logger: Object or name of logger to replace handlers.
        handlers: Object or name of logger from which to get handlers.
    """
    # Resolve logger
    if isinstance(logger, str):
        logger = get_logger(logger)
    if not isinstance(logger, logging.Logger):
        raise ValueError("Expected logger to be logger name or Logger object.")

    # Resolve handlers
    if isinstance(handlers, str):
        handlers = get_logger(handlers).handlers
    elif isinstance(handlers, logging.Logger):
        handlers = handlers.handlers
    else:
        raise ValueError("Expected handlers to be list, logger name or Logger object.")

    ## Replace handlers ##
    logger.handlers = list(handlers)


def add_file_handler(
    logger: logging.Logger,
    file_path: str,
    format: str = reconplogger_format,
    level: Optional[str] = "DEBUG",
) -> logging.FileHandler:
    """Adds a file handler to a given logger.

    Args:
        logger: Logger object where to add the file handler.
        file_path: Path to log file for handler.
        format: Format for logging.
        level: Logging level for the handler.

    Returns:
        The handler object which could be used for removeHandler.
    """
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(logging.Formatter(format))
    if level is not None:
        if level not in logging_levels:
            raise ValueError('Invalid logging level: "' + str(level) + '".')
        file_handler.setLevel(logging_levels[level])
    logger.addHandler(file_handler)
    return file_handler


def test_logger(logger: logging.Logger):
    """Logs one message to each debug, info and warning levels intended for testing."""
    logger.debug("reconplogger test debug message.")
    logger.info("reconplogger test info message.")
    logger.warning("reconplogger test warning message.")


def get_logger(logger_name: str) -> logging.Logger:
    """Returns an already existing logger.

    Args:
        logger_name:  Name of the logger to get.

    Returns:
        The logger object.

    Raises:
        ValueError: If the logger does not exist.
    """
    if (
        logger_name not in logging.Logger.manager.loggerDict
        and logger_name not in logging.root.manager.loggerDict
    ):
        raise ValueError('Logger "' + str(logger_name) + '" not defined.')
    return logging.getLogger(logger_name)


def logger_setup(
    logger_name: str = "plain_logger",
    config: Optional[str] = None,
    level: Optional[str] = None,
    env_prefix: str = "LOGGER",
    reload: bool = False,
    parent: Optional[logging.Logger] = None,
    init_messages: bool = False,
) -> logging.Logger:
    """Sets up logging configuration and returns the logger.

    Args:
        logger_name:  Name of the logger that needs to be used.
        config: Configuration string or path to configuration file or configuration file via environment variable.
        level: Optional logging level that overrides one in config.
        env_prefix: Environment variable names prefix for overriding logger configuration.
        reload: Whether to reload logging configuration overriding any previous settings.
        parent: Set for logging delegation to the parent.
        init_messages: Whether to log init and test messages.

    Returns:
        The logger object.
    """
    if not isinstance(env_prefix, str) or not env_prefix:
        raise ValueError("env_prefix is required to be a non-empty string.")
    env_cfg = env_prefix + "_CFG"
    env_name = env_prefix + "_NAME"
    env_level = env_prefix + "_LEVEL"

    # Configure logging
    load_config(os.getenv(env_cfg, config), reload=reload)

    # Get logger
    name = os.getenv(env_name, logger_name)
    logger = get_logger(name)
    if getattr(logger, "_reconplogger_setup", False) and not reload:
        if parent or level or init_messages:
            logger.debug(
                f"logger {name} already setup by reconplogger, ignoring overriding parameters."
            )
        return logger

    # Override parent
    logger.parent = parent

    # Override log level if set
    if env_level in os.environ:
        level = os.getenv(env_level)
    if level:
        if isinstance(level, str):
            if level not in logging_levels:
                raise ValueError('Invalid logging level: "' + str(level) + '".')
            level = logging_levels[level]
        else:
            raise ValueError("Expected level argument to be a string.")
        for handler in logger.handlers:
            if not isinstance(handler, logging.FileHandler):
                handler.setLevel(level)

    # Add correlation id filter
    logger.addFilter(_CorrelationIdLoggingFilter())

    # Log configured done and test logger
    if init_messages:
        logger.info("reconplogger (v" + __version__ + ") logger configured.")
        test_logger(logger)

    logger._reconplogger_setup = True
    return logger


flask_request_completed_skip_endpoints = set()


def flask_app_logger_setup(
    flask_app,
    logger_name: str = "plain_logger",
    config: Optional[str] = None,
    level: Optional[str] = None,
    env_prefix: str = "LOGGER",
    parent: Optional[logging.Logger] = None,
) -> logging.Logger:
    """Sets up logging configuration, configures flask to use it, and returns the logger.

    Args:
        flask_app (flask.app.Flask): The flask app object.
        logger_name:  Name of the logger that needs to be used.
        config: Configuration string or path to configuration file or configuration file via environment variable.
        level: Optional logging level that overrides one in config.
        env_prefix: Environment variable names prefix for overriding logger configuration.
        parent: Set for logging delegation to the parent.

    Returns:
        The logger object.
    """
    # Configure logging and get logger
    logger = logger_setup(
        logger_name=logger_name,
        config=config,
        level=level,
        env_prefix=env_prefix,
        parent=parent,
    )
    is_json_logger = logger.handlers[0].formatter.__class__.__name__ == "JsonFormatter"

    # Setup flask logger
    replace_logger_handlers(flask_app.logger, logger)
    flask_app.logger.setLevel(logger.level)
    flask_app.logger.parent = logger.parent

    # Add flask before and after request functions to augment the logs
    def _flask_logging_before_request():
        g.correlation_id = request.headers.get(
            "Correlation-ID", None
        )  # pylint: disable=assigning-non-slot
        g.start_time = time.time()  # pylint: disable=assigning-non-slot

    flask_app.before_request_funcs.setdefault(None, []).append(
        _flask_logging_before_request
    )

    def _flask_logging_after_request(response):
        if g.correlation_id:
            response.headers.set("Correlation-ID", g.correlation_id)
        if request.path not in flask_request_completed_skip_endpoints:
            if is_json_logger:
                message = "Request completed"
            else:
                message = (
                    f"{request.remote_addr} {request.method} {request.path} "
                    f'{request.environ.get("SERVER_PROTOCOL")} {response.status_code}'
                )
            flask_app.logger.info(
                message,
                extra={
                    "http_endpoint": request.path,
                    "http_method": request.method,
                    "http_response_code": response.status_code,
                    "http_response_size": response.calculate_content_length(),
                    "http_input_payload_size": request.content_length or 0,
                    "http_input_payload_type": request.content_type or "",
                    "http_response_time_ms": f"{1000*(time.time() - g.start_time):.0f}",
                },
            )

        return response

    flask_app.after_request_funcs.setdefault(None, []).append(
        _flask_logging_after_request
    )

    # Add correlation id filter
    flask_app.logger.addFilter(_CorrelationIdLoggingFilter())

    # Setup werkzeug logger at least at WARNING level in case its server is used
    # since it also logs at INFO level after each request creating redundancy
    werkzeug_logger = logging.getLogger("werkzeug")
    replace_logger_handlers(werkzeug_logger, logger)
    werkzeug_logger.setLevel(max(logger.level, WARNING))
    werkzeug_logger.parent = logger.parent
    import werkzeug._internal

    werkzeug._internal._logger = werkzeug_logger

    return logger


def get_correlation_id() -> str:
    """Returns the current correlation id.

    Raises:
        ImportError: When flask package not available.
        RuntimeError: When run outside an application context or if flask app has not been setup.
    """
    correlation_id = current_correlation_id.get()
    if correlation_id is not None:
        return correlation_id
    if find_spec("flask") is None:
        raise RuntimeError("get_correlation_id used outside correlation_id_context.")

    try:
        has_correlation_id = hasattr(g, "correlation_id")
    except RuntimeError:
        raise RuntimeError(
            "get_correlation_id used outside correlation_id_context or flask app context."
        )
    if not has_correlation_id:
        raise RuntimeError(
            "correlation_id not found in flask.g, probably flask app not yet setup."
        )
    return g.correlation_id


def set_correlation_id(correlation_id: str):
    """Sets the correlation id for the current application context.

    Raises:
        ImportError: When flask package not available.
        RuntimeError: When run outside an application context or if flask app has not been setup.
    """
    from flask import g

    try:
        hasattr(g, "correlation_id")
    except RuntimeError:
        raise RuntimeError(
            "set_correlation_id only intended to be used inside an application context."
        )
    g.correlation_id = str(correlation_id)  # pylint: disable=assigning-non-slot


current_correlation_id: ContextVar[Optional[str]] = ContextVar(
    "current_correlation_id", default=None
)


@contextmanager
def correlation_id_context(correlation_id: Optional[str]):
    """Context manager to set the correlation id for the current application context.

    Use as `with correlation_id_context(correlation_id): ...`. Calls to
    `get_correlation_id()` will return the correlation id set for the context.

    Args:
        correlation_id: The correlation id to set in the context.
    """
    token = current_correlation_id.set(correlation_id)
    try:
        yield
    finally:
        current_correlation_id.reset(token)


class _CorrelationIdLoggingFilter(logging.Filter):
    def filter(self, record):
        correlation_id = current_correlation_id.get()
        if correlation_id is not None:
            record.correlation_id = correlation_id
        elif find_spec("flask") and has_request_context():
            record.correlation_id = g.correlation_id
        return True


class RLoggerProperty:
    """Class designed to be inherited by other classes to add an rlogger property."""

    def __init__(self, *args, **kwargs):
        """Initializer for LoggerProperty class."""
        super().__init__(*args, **kwargs)
        if not hasattr(self, "_rlogger"):
            self.rlogger = True

    @property
    def rlogger(self):
        """The logger property for the class.

        :getter: Returns the current logger.
        :setter: Sets the reconplogger logger if True or sets null_logger if False or sets the given logger.

        Raises:
            ValueError: If an invalid logger value is given.
        """
        return self._rlogger

    @rlogger.setter
    def rlogger(self, logger: Optional[Union[bool, logging.Logger]]):
        if logger is None or (isinstance(logger, bool) and not logger):
            self._rlogger = null_logger
        elif isinstance(logger, bool) and logger:
            self._rlogger = logger_setup()
        else:
            self._rlogger = logger
