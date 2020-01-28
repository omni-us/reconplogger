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
        reconplogger.load_config('reconplogger_default')
        logger = logging.getLogger('plain_logger')
        info_msg = 'info message'
        with LogCapture() as log:
            logger.info(info_msg)
            log.check(('plain_logger', 'INFO', info_msg))

    def test_log_level(self):
        """Test load config with the default config and plain logger changing the log level."""
        reconplogger.load_config('reconplogger_default')
        logger = logging.getLogger('plain_logger')
        logger.setLevel(logging.ERROR)
        info_msg = 'info message'
        error_msg = 'error message'
        with LogCapture() as log:
            logger.info(info_msg)
            logger.error(error_msg)
            log.check(('plain_logger', 'ERROR', error_msg))

    def test_default_logger_with_exception(self):
        """Test exception logging with the default config and json logger."""
        reconplogger.load_config('reconplogger_default')
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

    def test_undefined_logger(self):
        """Test setting up a logger not already defined."""
        os.environ['LOGGER_NAME'] = 'undefined_logger'
        self.assertRaises(ValueError, lambda: reconplogger.logger_setup(None, 'LOGGER_NAME'))
        del os.environ['LOGGER_NAME']

    def test_flask_app_logger_setup(self):
        """Test flask app logger setup with json logger."""
        os.environ['LOGGER_CFG'] = 'reconplogger_default'
        os.environ['LOGGER_NAME'] = 'json_logger'
        app = Flask(__name__)
        reconplogger.flask_app_logger_setup('LOGGER_CFG', 'LOGGER_NAME', app)
        flask_msg = 'flask message'
        werkzeug_msg = 'werkzeug message'
        with LogCapture() as log:
            app.logger.warning(flask_msg)  # pylint: disable=no-member
            logging.getLogger('werkzeug').warning(werkzeug_msg)
            log.check_present(
                ('json_logger', 'WARNING', flask_msg),
                ('werkzeug', 'WARNING', werkzeug_msg),
            )
        del os.environ['LOGGER_CFG']
        del os.environ['LOGGER_NAME']


def run_tests():
    tests = unittest.defaultTestLoader.loadTestsFromTestCase(TestReconplogger)
    return unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == "__main__":
    unittest.main(verbosity=2)
