#!/usr/bin/env python3

import logging
import os
import reconplogger
import random
import shutil
import sys
import tempfile
import threading
import unittest
import uuid
from contextlib import ExitStack, contextmanager
from io import StringIO
from unittest.mock import patch
from typing import Iterator

from testfixtures import LogCapture, compare, Comparison

try:
    from flask import Flask, request
except ImportError:
    Flask = None
try:
    import requests
    from werkzeug.serving import make_server
except ImportError:
    requests = None


@contextmanager
def capture_logs(logger: logging.Logger) -> Iterator[StringIO]:
    with ExitStack() as stack:
        captured = StringIO()
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                stack.enter_context(patch.object(handler, "stream", captured))
        yield captured


class TestReconplogger(unittest.TestCase):
    def setUp(self):
        reconplogger.configs_loaded = set()

    def test_default_logger(self):
        """Test load config with the default config and plain logger."""
        reconplogger.load_config("reconplogger_default_cfg")
        logger = logging.getLogger("plain_logger")
        info_msg = "info message"
        with LogCapture(names="plain_logger") as log:
            logger.info(info_msg)
            log.check(("plain_logger", "INFO", info_msg))

    def test_log_level(self):
        """Test load config with the default config and plain logger changing the log level."""
        logger = reconplogger.logger_setup(level="INFO", reload=True)
        self.assertEqual(logger.handlers[0].level, logging.INFO)
        logger = reconplogger.logger_setup(level="ERROR", reload=True)
        self.assertEqual(logger.handlers[0].level, logging.ERROR)
        with patch.dict(os.environ, {"LOGGER_LEVEL": "WARNING"}):
            logger = reconplogger.logger_setup(
                level="INFO", env_prefix="LOGGER", reload=True
            )
            self.assertEqual(logger.handlers[0].level, logging.WARNING)

    def test_default_logger_with_exception(self):
        """Test exception logging with the default config and json logger."""
        reconplogger.load_config("reconplogger_default_cfg")
        logger = logging.getLogger("json_logger")
        error_msg = "error message"
        exception = RuntimeError("Exception message")
        with LogCapture(names="json_logger") as log:
            try:
                raise exception
            except Exception:
                logger.error(error_msg, exc_info=True)
                compare(Comparison(exception), log.records[-1].exc_info[1])
                log.check(("json_logger", "ERROR", error_msg))

    def test_plain_logger_setup(self):
        """Test logger_setup without specifying environment variable names."""
        logger = reconplogger.logger_setup()
        info_msg = "info message"
        with LogCapture(names="plain_logger") as log:
            logger.info(info_msg)
            log.check(("plain_logger", "INFO", info_msg))

    def test_json_logger_setup(self):
        """Test logger_setup without specifying environment variable names but changing logger name."""
        logger = reconplogger.logger_setup(logger_name="json_logger")
        info_msg = "info message"
        with LogCapture(names="json_logger") as log:
            logger.info(info_msg)
            log.check(("json_logger", "INFO", info_msg))

    def test_replace_logger_handlers(self):
        logger = logging.getLogger("test_replace_logger_handlers")
        handlers1 = reconplogger.logger_setup(logger_name="plain_logger").handlers
        handlers2 = reconplogger.logger_setup(logger_name="json_logger").handlers

        self.assertNotEqual(logger.handlers, handlers1)
        self.assertNotEqual(logger.handlers, handlers2)

        reconplogger.replace_logger_handlers(
            "test_replace_logger_handlers", "plain_logger"
        )
        self.assertEqual(logger.handlers, handlers1)
        self.assertNotEqual(logger.handlers, handlers2)

        reconplogger.replace_logger_handlers(
            "test_replace_logger_handlers", "json_logger"
        )
        self.assertEqual(logger.handlers, handlers2)
        self.assertNotEqual(logger.handlers, handlers1)

        self.assertRaises(
            ValueError, lambda: reconplogger.replace_logger_handlers(logger, False)
        )
        self.assertRaises(
            ValueError, lambda: reconplogger.replace_logger_handlers(False, False)
        )

    def test_init_messages(self):
        logger = reconplogger.logger_setup(init_messages=True, reload=True)
        with self.assertLogs(logger="plain_logger", level="WARNING") as log:
            reconplogger.test_logger(logger)
            self.assertTrue(
                any(["WARNING" in v and "reconplogger" in v for v in log.output])
            )

    @patch.dict(
        os.environ,
        {
            "RECONPLOGGER_NAME": "example_logger",
            "RECONPLOGGER_CFG": """{
            "version": 1,
            "formatters": {
                "verbose": {
                    "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
                }
            },
            "handlers": {
                "console":{
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "verbose"
                }
            },
            "loggers": {
                "example_logger": {
                    "handlers": ["console"],
                    "level": "DEBUG"
                }
            }
        }""",
        },
    )
    def test_logger_setup_env_prefix(self):
        logger = reconplogger.logger_setup(env_prefix="RECONPLOGGER")
        info_msg = "info message env logger"
        with LogCapture(names="example_logger") as log:
            logger.info(info_msg)
            log.check(("example_logger", "INFO", info_msg))

    def test_logger_setup_env_prefix_invalid(self):
        for env_prefix in [None, ""]:
            with self.subTest(env_prefix):
                with self.assertRaises(ValueError):
                    reconplogger.logger_setup(env_prefix=env_prefix)

    def test_undefined_logger(self):
        """Test setting up a logger not already defined."""
        self.assertRaises(
            ValueError, lambda: reconplogger.logger_setup("undefined_logger")
        )

    def test_logger_setup_invalid_level(self):
        with self.assertRaises(ValueError):
            reconplogger.logger_setup(level="INVALID", reload=True)
        with self.assertRaises(ValueError):
            reconplogger.logger_setup(level=True, reload=True)

    @patch.dict(os.environ, {"LOGGER_NAME": "json_logger"})
    def test_correlation_id_context(self):
        logger = reconplogger.logger_setup()
        correlation_id = str(uuid.uuid4())
        with reconplogger.correlation_id_context(correlation_id):
            self.assertEqual(correlation_id, reconplogger.get_correlation_id())
            with capture_logs(logger) as logs:
                logger.error("error message")
                self.assertIn(correlation_id, logs.getvalue())

    def test_get_correlation_id_outside_of_context(self):
        with patch("reconplogger.find_spec", return_value=None):
            self.assertIsNone(reconplogger.find_spec("flask"))
            with self.assertRaises(RuntimeError) as ctx:
                reconplogger.get_correlation_id()
            self.assertIn("used outside correlation_id_context", str(ctx.exception))

    @unittest.skipIf(not Flask, "flask package is required")
    @patch.dict(
        os.environ,
        {
            "RECONPLOGGER_CFG": "reconplogger_default_cfg",
            "RECONPLOGGER_NAME": "json_logger",
        },
    )
    def test_flask_app_logger_setup(self):
        app = Flask(__name__)
        reconplogger.flask_app_logger_setup(env_prefix="RECONPLOGGER", flask_app=app)
        assert app.logger.filters  # pylint: disable=no-member
        assert app.before_request_funcs
        assert app.after_request_funcs
        flask_msg = "flask message"
        werkzeug_msg = "werkzeug message"
        with LogCapture(names=(app.logger.name, "werkzeug")) as log:
            app.logger.warning(flask_msg)  # pylint: disable=no-member
            logging.getLogger("werkzeug").warning(werkzeug_msg)
            log.check_present(
                (app.logger.name, "WARNING", flask_msg),
                ("werkzeug", "WARNING", werkzeug_msg),
            )

    @unittest.skipIf(not Flask, "flask package is required")
    @patch.dict(
        os.environ,
        {
            "RECONPLOGGER_CFG": "reconplogger_default_cfg",
            "RECONPLOGGER_NAME": "json_logger",
        },
    )
    def test_flask_app_correlation_id(self):
        app = Flask(__name__)
        flask_msg = "flask message with correlation id"

        @app.route("/")
        def hello_world():
            if request.args.get("id") is None:
                correlation_id = reconplogger.get_correlation_id()
            else:
                correlation_id = request.args.get("id")
                reconplogger.set_correlation_id(correlation_id)
            app.logger.info(flask_msg)  # pylint: disable=no-member
            return "correlation_id=" + str(correlation_id)

        client = app.test_client()
        with LogCapture(
            names=app.logger.name, attributes=("name", "levelname")
        ) as logs:
            response = client.get("/")
            logs.check((app.logger.name, "ERROR"))
        self.assertEqual(response.status_code, 500)

        reconplogger.flask_app_logger_setup(env_prefix="RECONPLOGGER", flask_app=app)
        client = app.test_client()

        self.assertRaises(RuntimeError, lambda: reconplogger.get_correlation_id())
        self.assertRaises(RuntimeError, lambda: reconplogger.set_correlation_id("id"))

        # Check correlation id propagation
        with LogCapture(
            names=app.logger.name,
            attributes=("name", "levelname", "getMessage", "correlation_id"),
        ) as logs:
            correlation_id = str(uuid.uuid4())
            response = client.get("/", headers={"Correlation-ID": correlation_id})
            self.assertEqual(
                response.data.decode("utf-8"), "correlation_id=" + correlation_id
            )
            logs.check(
                (app.logger.name, "INFO", flask_msg, correlation_id),
                (app.logger.name, "INFO", "Request completed", correlation_id),
            )
        # Check missing correlation id
        with LogCapture(
            names=app.logger.name,
            attributes=("name", "levelname", "getMessage", "correlation_id"),
        ) as logs:
            client.get("/")
            correlation_id = logs.actual()[0][3]
            self.assertIsNone(correlation_id)
            logs.check(
                (app.logger.name, "INFO", flask_msg, correlation_id),
                (app.logger.name, "INFO", "Request completed", correlation_id),
            )
        # Check set correlation id
        with LogCapture(
            names=app.logger.name,
            attributes=("name", "levelname", "getMessage", "correlation_id"),
        ) as logs:
            correlation_id = str(uuid.uuid4())
            response = client.get("/?id=" + correlation_id)
            self.assertEqual(
                response.data.decode("utf-8"), "correlation_id=" + correlation_id
            )
            logs.check(
                (app.logger.name, "INFO", flask_msg, correlation_id),
                (app.logger.name, "INFO", "Request completed", correlation_id),
            )

    @unittest.skipIf(not Flask, "flask package is required")
    @unittest.skipIf(not requests, "requests and werkzeug packages are required")
    def test_requests_patch(self):
        app = Flask(__name__)
        logger = reconplogger.flask_app_logger_setup(app)

        @app.route("/id")
        def get_id():
            return reconplogger.get_correlation_id()

        port = random.randint(5000, 10000)
        server = make_server("localhost", port, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        werkzeug_logger = logging.getLogger("werkzeug")
        self.assertEqual(werkzeug_logger.handlers, logger.handlers)
        self.assertGreaterEqual(werkzeug_logger.level, reconplogger.WARNING)

        correlation_id = str(uuid.uuid4())
        with reconplogger.correlation_id_context(correlation_id):
            response = requests.get(f"http://localhost:{port}/id")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(correlation_id, response.text)
            self.assertEqual(correlation_id, response.headers["Correlation-ID"])

        with app.test_request_context():
            correlation_id = str(uuid.uuid4())
            reconplogger.set_correlation_id(correlation_id)
            response = requests.get(f"http://localhost:{port}/id")
            self.assertEqual(correlation_id, response.text)
            self.assertEqual(correlation_id, response.headers["Correlation-ID"])

        server.shutdown()

    def test_add_file_handler(self):
        """Test the use of add_file_handler."""
        tmpdir = tempfile.mkdtemp(prefix="_reconplogger_test_")
        error_msg = "error message"
        debug_msg = "debug message"

        log_file = os.path.join(tmpdir, "file1.log")
        logger = reconplogger.logger_setup(logger_name="plain_logger", level="ERROR")
        reconplogger.add_file_handler(logger, file_path=log_file, level="DEBUG")
        self.assertEqual(logger.handlers[0].level, logging.ERROR)
        self.assertEqual(logger.handlers[1].level, logging.DEBUG)
        logger.error(error_msg)
        logger.debug(debug_msg)
        logger.handlers[1].close()
        self.assertTrue(any([error_msg in line for line in open(log_file).readlines()]))
        self.assertTrue(any([debug_msg in line for line in open(log_file).readlines()]))

        log_file = os.path.join(tmpdir, "file2.log")
        logger = reconplogger.logger_setup(
            logger_name="plain_logger", level="DEBUG", reload=True
        )
        reconplogger.add_file_handler(logger, file_path=log_file, level="ERROR")
        self.assertEqual(logger.handlers[0].level, logging.DEBUG)
        self.assertEqual(logger.handlers[1].level, logging.ERROR)
        logger.error(error_msg)
        logger.debug(debug_msg)
        logger.handlers[1].close()
        self.assertTrue(any([error_msg in line for line in open(log_file).readlines()]))
        self.assertFalse(
            any([debug_msg in line for line in open(log_file).readlines()])
        )

        self.assertRaises(
            ValueError,
            lambda: reconplogger.add_file_handler(
                logger, file_path=log_file, level="INVALID"
            ),
        )

        shutil.rmtree(tmpdir)

    def test_logger_property(self):
        class MyClass(reconplogger.RLoggerProperty):
            pass

        myclass = MyClass()
        myclass.rlogger = False
        self.assertEqual(myclass.rlogger, reconplogger.null_logger)
        myclass.rlogger = True
        self.assertEqual(myclass.rlogger, reconplogger.logger_setup())
        logger = logging.Logger("test_logger_property")
        myclass.rlogger = logger
        self.assertEqual(myclass.rlogger, logger)


def run_tests():
    tests = unittest.defaultTestLoader.loadTestsFromTestCase(TestReconplogger)
    if not unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful():
        sys.exit(True)


if __name__ == "__main__":
    run_tests()
