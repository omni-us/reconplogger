#!/usr/bin/env python3

import os
import sys
import unittest
import shutil
import tempfile
import logging
import uuid
import reconplogger
from testfixtures import LogCapture, compare, Comparison
from flask import Flask, request
import requests


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
        self.assertEqual(logger.handlers[0].level, logging.INFO)
        logger = reconplogger.logger_setup(level='ERROR')
        self.assertEqual(logger.handlers[0].level, logging.ERROR)
        os.environ['LOGGER_LEVEL'] = 'WARNING'
        logger = reconplogger.logger_setup(level='INFO', env_prefix='LOGGER')
        self.assertEqual(logger.handlers[0].level, logging.WARNING)
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

    def test_replace_logger_handlers(self):
        logger = logging.getLogger('test_replace_logger_handlers')
        handlers1 = reconplogger.logger_setup(logger_name='plain_logger').handlers
        handlers2 = reconplogger.logger_setup(logger_name='json_logger').handlers

        self.assertNotEqual(logger.handlers, handlers1)
        self.assertNotEqual(logger.handlers, handlers2)

        reconplogger.replace_logger_handlers('test_replace_logger_handlers', 'plain_logger')
        self.assertEqual(logger.handlers, handlers1)
        self.assertNotEqual(logger.handlers, handlers2)

        reconplogger.replace_logger_handlers('test_replace_logger_handlers', 'json_logger')
        self.assertEqual(logger.handlers, handlers2)
        self.assertNotEqual(logger.handlers, handlers1)

        self.assertRaises(
            ValueError, lambda: reconplogger.replace_logger_handlers(logger, False))
        self.assertRaises(
            ValueError, lambda: reconplogger.replace_logger_handlers(False, False))

    def test_init_messages(self):
        logger = reconplogger.logger_setup(init_messages=True)
        with self.assertLogs(level='WARNING') as log:
            reconplogger.test_logger(logger)
            self.assertTrue(any(['WARNING' in v and 'reconplogger' in v for v in log.output]))

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

    def test_logger_setup_invalid_level(self):
        self.assertRaises(
            ValueError, lambda: reconplogger.logger_setup(level='INVALID'))
        self.assertRaises(
            ValueError, lambda: reconplogger.logger_setup(level=True))

    def test_flask_app_logger_setup(self):
        """Test flask app logger setup with json logger."""
        env_prefix = 'RECONPLOGGER'
        os.environ['RECONPLOGGER_CFG'] = 'reconplogger_default_cfg'
        os.environ['RECONPLOGGER_NAME'] = 'json_logger'
        app = Flask(__name__)
        reconplogger.flask_app_logger_setup(
            env_prefix=env_prefix, flask_app=app)
        assert app.logger.filters  # pylint: disable=no-member
        assert app.before_request_funcs
        assert app.after_request_funcs
        flask_msg = 'flask message'
        werkzeug_msg = 'werkzeug message'
        with LogCapture() as log:
            app.logger.warning(flask_msg)  # pylint: disable=no-member
            logging.getLogger('werkzeug').warning(werkzeug_msg)
            log.check_present(
                (app.logger.name, 'WARNING', flask_msg),
                ('werkzeug', 'WARNING', werkzeug_msg),
            )
        del os.environ['RECONPLOGGER_CFG']
        del os.environ['RECONPLOGGER_NAME']

    def test_flask_app_correlation_id(self):
        """Test that the flask logs contains the correct correlation id"""
        env_prefix = 'RECONPLOGGER'
        os.environ['RECONPLOGGER_CFG'] = 'reconplogger_default_cfg'
        os.environ['RECONPLOGGER_NAME'] = 'json_logger'
        app = Flask(__name__)
        flask_msg = 'flask message with correlation id'

        @app.route('/')
        def hello_world():
            if request.args.get('id') is None:
                correlation_id = reconplogger.get_correlation_id()
            else:
                correlation_id = request.args.get('id')
                reconplogger.set_correlation_id(correlation_id)
            app.logger.info(flask_msg)  # pylint: disable=no-member
            return 'correlation_id='+correlation_id

        client = app.test_client()
        with LogCapture(attributes=('name', 'levelname')) as logs:
            response = client.get("/")
            logs.check((app.logger.name, 'ERROR'))
        self.assertEqual(response.status_code, 500)

        reconplogger.flask_app_logger_setup(
            env_prefix=env_prefix, flask_app=app)
        client = app.test_client()

        self.assertRaises(RuntimeError, lambda: reconplogger.get_correlation_id())
        self.assertRaises(RuntimeError, lambda: reconplogger.set_correlation_id('id'))

        # Check correlation id propagation
        with LogCapture(attributes=('name', 'levelname', 'getMessage', 'correlation_id')) as logs:
            correlation_id = str(uuid.uuid4())
            response = client.get("/", headers={'Correlation-ID': correlation_id})
            self.assertEqual(response.data.decode('utf-8'), 'correlation_id='+correlation_id)
            logs.check(
                (app.logger.name, 'INFO', flask_msg, correlation_id),
                (app.logger.name, 'INFO', "Request is completed", correlation_id),
            )
        # Check correlation id creation
        with LogCapture(attributes=('name', 'levelname', 'getMessage', 'correlation_id')) as logs:
            client.get("/")
            correlation_id = logs.actual()[0][3]
            uuid.UUID(correlation_id)
            logs.check(
                (app.logger.name, 'INFO', flask_msg, correlation_id),
                (app.logger.name, 'INFO', "Request is completed", correlation_id),
            )
        # Check set correlation id
        with LogCapture(attributes=('name', 'levelname', 'getMessage', 'correlation_id')) as logs:
            correlation_id = str(uuid.uuid4())
            response = client.get("/?id="+correlation_id)
            self.assertEqual(response.data.decode('utf-8'), 'correlation_id='+correlation_id)
            logs.check(
                (app.logger.name, 'INFO', flask_msg, correlation_id),
                (app.logger.name, 'INFO', "Request is completed", correlation_id),
            )

        del os.environ['RECONPLOGGER_CFG']
        del os.environ['RECONPLOGGER_NAME']

    @unittest.mock.patch("requests.sessions.Session.request_orig")
    @unittest.mock.patch("reconplogger.g", spec={}) # https://github.com/pallets/flask/issues/3637 adding spec as workaround for a python 3.8 bug
    @unittest.mock.patch("reconplogger.has_request_context", return_value=True)
    def test_requests_patch(self, mock_has_request_context, mock_g, mock_request_orig):
        mock_g.correlation_id = uuid.uuid4()
        requests.get("http://dummy")
        mock_request_orig.assert_called_once_with(
            allow_redirects=True, headers={'Correlation-ID': mock_g.correlation_id},
            method='get', params=None, url='http://dummy')

    def test_add_file_handler(self):
        """Test the use of add_file_handler."""
        tmpdir = tempfile.mkdtemp(prefix='_reconplogger_test_')
        error_msg = 'error message'
        debug_msg = 'debug message'

        log_file = os.path.join(tmpdir, 'file1.log')
        logger = reconplogger.logger_setup(logger_name='plain_logger', level='ERROR')
        reconplogger.add_file_handler(logger, file_path=log_file, level='DEBUG')
        self.assertEqual(logger.handlers[0].level, logging.ERROR)
        self.assertEqual(logger.handlers[1].level, logging.DEBUG)
        logger.error(error_msg)
        logger.debug(debug_msg)
        logger.handlers[1].close()
        self.assertTrue(any([error_msg in line for line in open(log_file).readlines()]))
        self.assertTrue(any([debug_msg in line for line in open(log_file).readlines()]))

        log_file = os.path.join(tmpdir, 'file2.log')
        logger = reconplogger.logger_setup(logger_name='plain_logger', level='DEBUG')
        reconplogger.add_file_handler(logger, file_path=log_file, level='ERROR')
        self.assertEqual(logger.handlers[0].level, logging.DEBUG)
        self.assertEqual(logger.handlers[1].level, logging.ERROR)
        logger.error(error_msg)
        logger.debug(debug_msg)
        logger.handlers[1].close()
        self.assertTrue(any([error_msg in line for line in open(log_file).readlines()]))
        self.assertFalse(any([debug_msg in line for line in open(log_file).readlines()]))

        self.assertRaises(
            ValueError, lambda: reconplogger.add_file_handler(logger, file_path=log_file, level='INVALID'))

        shutil.rmtree(tmpdir)

    def test_logger_property(self):
        class MyClass(reconplogger.RLoggerProperty):
            pass

        myclass = MyClass()
        myclass.rlogger = False
        self.assertEqual(myclass.rlogger, reconplogger.null_logger)
        myclass.rlogger = True
        self.assertEqual(myclass.rlogger, reconplogger.logger_setup())
        logger = logging.Logger('test_logger_property')
        myclass.rlogger = logger
        self.assertEqual(myclass.rlogger, logger)


def run_tests():
    tests = unittest.defaultTestLoader.loadTestsFromTestCase(TestReconplogger)
    if not unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful():
        sys.exit(True)


def run_test_coverage():
    try:
        import coverage
    except:
        print('error: coverage package not found, run_test_coverage requires it.')
        sys.exit(True)
    cov = coverage.Coverage(source=['reconplogger'])
    cov.start()
    del sys.modules['reconplogger']
    import reconplogger
    run_tests()
    cov.stop()
    cov.save()
    cov.report()
    if 'xml' in sys.argv:
        outfile = sys.argv[sys.argv.index('xml')+1]
        cov.xml_report(outfile=outfile)
        print('\nSaved coverage report to '+outfile+'.')
    else:
        cov.html_report(directory='htmlcov')
        print('\nSaved html coverage report to htmlcov directory.')


if __name__ == '__main__':
    if 'coverage' in sys.argv:
        run_test_coverage()
    else:
        run_tests()
