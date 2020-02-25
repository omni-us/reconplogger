#!/usr/bin/env python3

import os
import unittest
import logging
import reconplogger
from testfixtures import LogCapture, compare, Comparison
from flask import Flask


class TestReconplogger(unittest.TestCase):
    def test_default_logger(self):
        """Test load config with the default config and plain logger."""
        reconplogger.load_config('reconplogger_default_cfg')
        logger = logging.getLogger('plain_logger')
        info_msg = 'info message'
        with LogCapture() as log:
            logger.info(info_msg)
            log.check(('plain_logger', 'INFO', info_msg))

    def test_log_level(self):
        """Test load config with the default config and plain logger changing the log level."""
        logger = reconplogger.logger_setup(level='INFO')
        self.assertEqual(logger.level, logging.INFO)
        logger = reconplogger.logger_setup(level='ERROR')
        self.assertEqual(logger.level, logging.ERROR)
        os.environ['LOGGER_LEVEL'] = 'WARNING'
        logger = reconplogger.logger_setup(level='INFO', env_prefix='LOGGER')
        self.assertEqual(logger.level, logging.WARNING)
        del os.environ['LOGGER_LEVEL']

    def test_default_logger_with_exception(self):
        """Test exception logging with the default config and json logger."""
        reconplogger.load_config('reconplogger_default_cfg')
        logger = logging.getLogger('json_logger')
        error_msg = 'error message'
        exception = RuntimeError('Exception message')
        with LogCapture() as log:
            try:
                raise exception
            except Exception as e:
                logger.error(error_msg, exc_info=True)
                compare(Comparison(exception), log.records[-1].exc_info[1])
                log.check(('json_logger', 'ERROR', error_msg))

    def test_plain_logger_setup(self):
        """Test logger_setup without specifying environment variable names."""
        logger = reconplogger.logger_setup()
        info_msg = 'info message'
        with LogCapture() as log:
            logger.info(info_msg)
            log.check(('plain_logger', 'INFO', info_msg))

    def test_json_logger_setup(self):
        """Test logger_setup without specifying environment variable names but changing logger name."""
        logger = reconplogger.logger_setup(logger_name='json_logger')
        info_msg = 'info message'
        with LogCapture() as log:
            logger.info(info_msg)
            log.check(('json_logger', 'INFO', info_msg))

    def test_logger_setup_env_prefix(self):
        """Test logger setup with specifying environment prefix."""
        env_prefix = 'RECONPLOGGER'
        os.environ['RECONPLOGGER_NAME'] = 'example_logger'
        os.environ['RECONPLOGGER_CFG'] = """{
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
        }"""
        logger = reconplogger.logger_setup(env_prefix=env_prefix)
        info_msg = 'info message env logger'
        with LogCapture() as log:
            logger.info(info_msg)
            log.check(('example_logger', 'INFO', info_msg))

        del os.environ['RECONPLOGGER_CFG']
        del os.environ['RECONPLOGGER_NAME']

        self.assertRaises(
            ValueError, lambda: reconplogger.logger_setup(env_prefix=None))
        self.assertRaises(
            ValueError, lambda: reconplogger.logger_setup(env_prefix=''))

    def test_undefined_logger(self):
        """Test setting up a logger not already defined."""
        self.assertRaises(
            ValueError, lambda: reconplogger.logger_setup('undefined_logger'))

    def test_flask_app_logger_setup(self):
        """Test flask app logger setup with json logger."""
        env_prefix = 'RECONPLOGGER'
        os.environ['RECONPLOGGER_CFG'] = 'reconplogger_default_cfg'
        os.environ['RECONPLOGGER_NAME'] = 'json_logger'
        app = Flask(__name__)
        reconplogger.flask_app_logger_setup(
            env_prefix=env_prefix, flask_app=app)
        flask_msg = 'flask message'
        werkzeug_msg = 'werkzeug message'
        with LogCapture() as log:
            app.logger.warning(flask_msg)  # pylint: disable=no-member
            logging.getLogger('werkzeug').warning(werkzeug_msg)
            log.check_present(
                ('json_logger', 'WARNING', flask_msg),
                ('werkzeug', 'WARNING', werkzeug_msg),
            )
        del os.environ['RECONPLOGGER_CFG']
        del os.environ['RECONPLOGGER_NAME']


def run_tests():
    tests = unittest.defaultTestLoader.loadTestsFromTestCase(TestReconplogger)
    return unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == "__main__":
    unittest.main(verbosity=2)
