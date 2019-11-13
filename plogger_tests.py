#!/usr/bin/env python3

import os
import unittest
import logging
import plogger
from testfixtures import LogCapture, compare, Comparison
from flask import Flask


class TestPlogger(unittest.TestCase):
    def test_default_logger(self):
        """Test load config with the default config and plain logger."""
        plogger.load_config('plogger_default')
        logger = logging.getLogger('plogger_plain')
        info_msg = 'info message'
        with LogCapture() as log:
            logger.info(info_msg)
            log.check( ('plogger_plain', 'INFO', info_msg) )

    def test_log_level(self):
        """Test load config with the default config and plain logger changing the log level."""
        plogger.load_config('plogger_default')
        logger = logging.getLogger('plogger_plain')
        logger.setLevel(logging.ERROR)
        info_msg = 'info message'
        error_msg = 'error message'
        with LogCapture() as log:
            logger.info(info_msg)
            logger.error(error_msg)
            log.check( ('plogger_plain', 'ERROR', error_msg) )

    def test_default_logger_with_exception(self):
        """Test exception logging with the default config and json logger."""
        plogger.load_config('plogger_default')
        logger = logging.getLogger('plogger_json')
        error_msg = 'error message'
        exception = RuntimeError('Exception message')
        with LogCapture() as log:
            try:
                raise exception
            except:
                logger.error(error_msg, exc_info=True)
                compare(Comparison(exception), log.records[-1].exc_info[1])
                log.check( ('plogger_json', 'ERROR', error_msg) )

    def test_flask_app_logger_setup(self):
        """Test flask app logger setup with json logger."""
        os.environ['PLOGGER_CFG'] = 'plogger_default'
        os.environ['PLOGGER_NAME'] = 'plogger_json'
        app = Flask(__name__)
        plogger.flask_app_logger_setup('PLOGGER_CFG', 'PLOGGER_NAME', app)
        flask_msg = 'flask message'
        werkzeug_msg = 'werkzeug message'
        with LogCapture() as log:
            app.logger.warning(flask_msg)  # pylint: disable=no-member
            logging.getLogger('werkzeug').warning(werkzeug_msg)
            log.check_present(
                ('plogger_json', 'WARNING', flask_msg),
                ('werkzeug', 'WARNING', werkzeug_msg),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
