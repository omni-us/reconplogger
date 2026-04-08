import datetime
import logging
import logging.config
import os
from contextlib import contextmanager
from contextvars import ContextVar
from importlib.util import find_spec
from logging import CRITICAL, DEBUG, ERROR, INFO, NOTSET, WARNING
from typing import Optional, Union

import pythonjsonlogger
import yaml

__version__ = "5.0.0.dev1"

__all__ = [
    "RLoggerProperty",
    "logger_setup",
    "flask_app_logger_setup",
    "get_correlation_id",
    "set_correlation_id",
    "correlation_id_context",
    "flask_request_completed_skip_endpoints",
    "add_file_handler",
    "null_logger",
]


if find_spec("flask"):
    from flask import g, request

flask_requests_patch = False
if find_spec("requests"):
    # Patch requests to forward the correlation ID on every outbound call.
    # Flask fallback (g.correlation_id) is used only when flask is installed and
    # a request context is active; otherwise current_correlation_id is used directly.
    import requests

    def _request_patch(slf, *args, **kwargs):
        headers = kwargs.pop("headers", {}) or {}
        correlation_id = current_correlation_id.get()
        if correlation_id is None and find_spec("flask"):
            try:
                from flask import g as _g
                from flask import has_request_context as _hrc

                if _hrc() and hasattr(_g, "correlation_id"):
                    correlation_id = _g.correlation_id
            except Exception:
                pass
        if correlation_id:
            headers["Correlation-ID"] = correlation_id
        return slf.request_orig(*args, **kwargs, headers=headers)

    requests.sessions.Session.request_orig = requests.sessions.Session.request
    requests.sessions.Session.request = _request_patch
    flask_requests_patch = True


reconplogger_format = "%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s"

reconplogger_default_cfg = {
    "version": 1,
    "formatters": {
        "plain": {
            "format": reconplogger_format,
        },
        "json": {
            "format": reconplogger_format.replace("asctime", "timestamp"),
            "class": "reconplogger.JsonFormatter",
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

# Internal state for singleton primary logger
_primary_logger: Optional[logging.Logger] = None

ENV_CFG = "LOGGER_CFG"
ENV_NAME = "LOGGER_NAME"
ENV_LEVEL = "LOGGER_LEVEL"
ENV_ROOT_HANDLER = "LOGGER_ROOT_HANDLER"
ENV_ROOT_LEVEL = "LOGGER_ROOT_LEVEL"


def reset_configs():
    """Resets reconplogger's internal configuration state.

    Clears the cached loaded configurations and the singleton primary logger so
    logging can be configured again from scratch.
    """
    global configs_loaded, _primary_logger
    configs_loaded = set()
    _primary_logger = None


def load_config(cfg: Optional[Union[str, dict]] = None):
    """Loads a logging configuration from path or environment variable or dictionary object.

    Args:
        cfg: Path to configuration file (json|yaml), or name of environment variable (json|yaml) or
            configuration object or None/"reconplogger_default_cfg" to use default configuration.

    Returns:
        The logging package object.
    """
    if cfg is None:
        cfg_dict = reconplogger_default_cfg
    elif isinstance(cfg, dict):
        cfg_dict = cfg
    elif cfg in {"", "reconplogger_default_cfg"} or (
        cfg in os.environ and os.environ[cfg] == "reconplogger_default_cfg"
    ):
        cfg_dict = reconplogger_default_cfg
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
                "Received string which is neither a path to an existing file nor the name of an "
                "set environment variable nor a python dictionary string that can be consumed by "
                "logging.config.dictConfig."
            )

    cfg_dict["disable_existing_loggers"] = False

    cfg_hash = yaml.safe_dump(cfg_dict).__hash__()
    if cfg_hash not in configs_loaded:
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


def get_logger(logger_name: str) -> logging.Logger:
    """Returns an already existing logger.

    Args:
        logger_name:  Name of the logger to get.

    Returns:
        The logger object.

    Raises:
        ValueError: If the logger does not exist.
    """
    if logger_name not in logging.Logger.manager.loggerDict and logger_name not in logging.root.manager.loggerDict:
        raise ValueError(f'Logger "{logger_name}" not defined.')
    return logging.getLogger(logger_name)


def logger_setup(
    logger_name: str = "plain_logger",
    config: Optional[str] = None,
    level: Optional[str] = None,
) -> logging.Logger:
    """Sets up logging configuration and returns the logger.

    If the environment variable ``LOGGER_ROOT_HANDLER`` is set to the name of a handler
    defined in the logging config, that handler is installed on the root logger so that
    all third-party loggers (which propagate to the root by default) are also captured.
    The primary logger level remains controlled by ``level`` / ``LOGGER_LEVEL``, while the
    root logger level can be controlled independently through ``LOGGER_ROOT_LEVEL``.
    On subsequent calls the same primary logger is returned without reconfiguring the root.
    To force a fresh configuration pass, call :func:`reset_configs` first.

    Args:
        logger_name:  Name of the logger that needs to be used.
        config: Configuration string or path to configuration file or configuration file via environment variable.
        level: Optional logging level that overrides one in config.

    Returns:
        The logger object.
    """
    global _primary_logger

    # Return primary logger on subsequent calls (singleton behaviour)
    if _primary_logger is not None:
        name = os.getenv(ENV_NAME, logger_name)
        if name != _primary_logger.name or config or level:
            _primary_logger.debug(
                "logger_setup called again with different arguments; returning existing primary logger."
            )
        return _primary_logger

    # Configure logging
    load_config(os.getenv(ENV_CFG, config))

    # Get logger
    name = os.getenv(ENV_NAME, logger_name)
    logger = get_logger(name)

    # Resolve the effective log level for the primary logger
    effective_level: Optional[int] = None
    if ENV_LEVEL in os.environ:
        level = os.getenv(ENV_LEVEL)
    if level:
        if level not in logging_levels:
            raise ValueError('Invalid logging level: "' + str(level) + '".')
        effective_level = logging_levels[level]

    _configure_root_logger()

    # Apply log level overrides to the named logger's handlers
    if effective_level is not None:
        for handler in logger.handlers:
            if not isinstance(handler, logging.FileHandler):
                handler.setLevel(effective_level)

    # Add correlation id filter
    logger.addFilter(_CorrelationIdLoggingFilter())

    logger._reconplogger_setup = True
    _primary_logger = logger
    return logger


def _configure_root_logger() -> None:
    """Installs a named handler on the root logger and removes stream handlers from named loggers.

    After this call every log record in the process flows through the single
    root handler, regardless of which named logger emitted it.  All named
    loggers (except those with only ``NullHandler`` instances) have their
    ``StreamHandler`` instances removed and ``propagate`` set to ``True`` so
    records bubble up to the root while keeping non-stream handlers such as
    file handlers attached.
    """
    handler_name = os.getenv(ENV_ROOT_HANDLER)
    if not handler_name:
        return

    # Retrieve the already-configured handler by name
    assert logging.root.manager.loggerDict  # just to verify config is loaded
    handler_obj = logging._handlers.get(handler_name)  # type: ignore[attr-defined]
    if handler_obj is None:
        raise ValueError(
            f'Handler "{handler_name}" not found in the logging configuration. '
            "Ensure the handler is defined in the config before setting LOGGER_ROOT_HANDLER."
        )

    root = logging.getLogger()
    root.handlers = [handler_obj]
    root_level_name = os.getenv(ENV_ROOT_LEVEL)
    level = handler_obj.level
    if root_level_name:
        if root_level_name not in logging_levels:
            raise ValueError('Invalid logging level: "' + str(root_level_name) + '".')
        level = logging_levels[root_level_name]
    handler_obj.setLevel(level)
    root.setLevel(level)

    logging.captureWarnings(True)

    # Remove stream handlers from named loggers so their remaining handlers, such
    # as FileHandler, keep working without duplicating root stream output.
    for lg_obj in logging.Logger.manager.loggerDict.values():
        if isinstance(lg_obj, logging.Logger):
            if any(isinstance(h, logging.NullHandler) for h in lg_obj.handlers):
                continue
            lg_obj.handlers = [
                handler
                for handler in lg_obj.handlers
                if not isinstance(handler, logging.StreamHandler) or isinstance(handler, logging.FileHandler)
            ]
            lg_obj.propagate = True


flask_request_completed_skip_endpoints = set()


def flask_app_logger_setup(
    flask_app,
    logger_name: str = "plain_logger",
    config: Optional[str] = None,
    level: Optional[str] = None,
) -> logging.Logger:
    """Sets up logging configuration, configures flask to use it, and returns the logger.

    Args:
        flask_app (flask.app.Flask): The flask app object.
        logger_name:  Name of the logger that needs to be used.
        config: Configuration string or path to configuration file or configuration file via environment variable.
        level: Optional logging level that overrides one in config.

    Returns:
        The logger object.
    """
    # Configure logging and get logger
    logger = logger_setup(
        logger_name=logger_name,
        config=config,
        level=level,
    )

    # Apply WSGI middleware to manage correlation ID at the transport layer
    flask_app.wsgi_app = CorrelationIdWsgiMiddleware(flask_app.wsgi_app)

    # Setup flask logger
    replace_logger_handlers(flask_app.logger, logger)
    flask_app.logger.setLevel(logger.level)

    # Add flask before and after request functions to augment the logs
    def _flask_logging_before_request():
        # current_correlation_id is already set by CorrelationIdWsgiMiddleware;
        # mirror it into g for compatibility with set_correlation_id / get_correlation_id.
        g.correlation_id = current_correlation_id.get()  # pylint: disable=assigning-non-slot

    flask_app.before_request_funcs.setdefault(None, []).append(_flask_logging_before_request)

    def _flask_logging_after_request(response):
        # Correlation-ID response header is injected by CorrelationIdWsgiMiddleware.
        if request.path not in flask_request_completed_skip_endpoints:
            message = (
                f"{request.remote_addr} {request.method} {request.path} "
                f"{request.environ.get('SERVER_PROTOCOL')} {response.status_code}"
            )
            flask_app.logger.info(message)

        return response

    flask_app.after_request_funcs.setdefault(None, []).append(_flask_logging_after_request)

    # Add correlation id filter
    flask_app.logger.addFilter(_CorrelationIdLoggingFilter())

    # Setup werkzeug logger at least at WARNING level in case its server is used
    # since it also logs at INFO level after each request creating redundancy
    werkzeug_logger = logging.getLogger("werkzeug")
    replace_logger_handlers(werkzeug_logger, logger)
    werkzeug_logger.setLevel(max(logger.level, WARNING))
    import werkzeug._internal

    werkzeug._internal._logger = werkzeug_logger

    return logger


if find_spec("flask"):

    class CorrelationIdWsgiMiddleware:
        """WSGI middleware that manages the correlation ID for Flask applications.

        Wraps the Flask WSGI app to:
        - Extract the ``Correlation-ID`` header from the incoming request (or leave it as ``None``).
        - Store it in :data:`current_correlation_id` for the duration of the request.
        - Inject the ``Correlation-ID`` into the response headers when one is present.

        Applied automatically by :func:`flask_app_logger_setup`.  Can also be applied
        manually::

            from reconplogger import CorrelationIdWsgiMiddleware
            app.wsgi_app = CorrelationIdWsgiMiddleware(app.wsgi_app)
        """

        def __init__(self, wsgi_app):
            self._app = wsgi_app

        def __call__(self, environ, start_response):
            correlation_id = environ.get("HTTP_CORRELATION_ID")
            token = current_correlation_id.set(correlation_id)

            def _start_response(status, headers, exc_info=None):
                if correlation_id:
                    headers = list(headers) + [("Correlation-ID", correlation_id)]
                return start_response(status, headers, exc_info)

            try:
                return self._app(environ, _start_response)
            finally:
                current_correlation_id.reset(token)


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
        raise RuntimeError("get_correlation_id used outside correlation_id_context or flask app context.")
    if not has_correlation_id:
        raise RuntimeError("correlation_id not found in flask.g, probably flask app not yet setup.")
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
        raise RuntimeError("set_correlation_id only intended to be used inside an application context.")
    g.correlation_id = str(correlation_id)  # pylint: disable=assigning-non-slot


current_correlation_id: ContextVar[Optional[str]] = ContextVar("current_correlation_id", default=None)


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
        elif find_spec("flask"):
            try:
                from flask import g as _g
                from flask import has_request_context as _hrc

                if _hrc() and hasattr(_g, "correlation_id"):
                    record.correlation_id = _g.correlation_id
            except Exception:
                pass
        return True


_unset = object()


class RLoggerProperty:
    """Class designed to be inherited by other classes to add an rlogger property."""

    def __init__(self, *args, **kwargs):
        """Initializer for LoggerProperty class."""
        rlogger = kwargs.pop("rlogger", _unset)
        super().__init__(*args, **kwargs)
        if rlogger is not _unset:
            self.rlogger = rlogger
        elif not hasattr(self, "_rlogger"):
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


class JsonFormatter(pythonjsonlogger.json.JsonFormatter):
    """JSON formatter from https://github.com/logmatic/logmatic-python/

    The MIT License (MIT)
    Copyright (c) 2017 Logmatic.io
    """

    def __init__(
        self,
        fmt=(
            "%(asctime) %(name) %(processName) %(filename)  %(funcName) %(levelname) %(lineno) "
            "%(module) %(threadName) %(message)"
        ),
        datefmt="%Y-%m-%dT%H:%M:%SZ%z",
        style="%",
        extra={},
        *args,
        **kwargs,
    ):
        self._extra = extra
        pythonjsonlogger.json.JsonFormatter.__init__(self, fmt=fmt, datefmt=datefmt, *args, **kwargs)

    def process_log_record(self, log_record):
        # Enforce the presence of a timestamp
        if "asctime" in log_record:
            log_record["timestamp"] = log_record["asctime"]
        else:
            log_record["timestamp"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if self._extra is not None:
            for key, value in self._extra.items():
                log_record[key] = value
        return super().process_log_record(log_record)
