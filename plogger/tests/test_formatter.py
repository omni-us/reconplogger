import unittest
from plogger.logger import Logger
import sys
import io


class TestPlogger(unittest.TestCase):
    def test_normal_logger(self):
        out = io.StringIO()
        LOGGER = Logger().get_logger()
        test_string = 'Hello World'
        LOGGER.info(test_string)
        output = out.getvalue().strip()
        if test_string in output:
            return True
        else:
            return False

    def test_json_logger(self):
        out = io.StringIO()
        LOGGER = Logger().get_logger(json=True)
        test_string = 'Hello World'
        LOGGER.info(test_string)
        output = out.getvalue().strip()
        if "message" in output:
            return True
        else:
            return False

    def test_logger_with_exception(self):
        try:
            out = io.StringIO()
            LOGGER = Logger().get_logger(json=True)
            a = 100
            b = 0
            c = a/b
        except Exception as e:
            LOGGER.error("Exception has occured", exc_info=True)
            output = out.getvalue().strip()
            if "ZeroDivisionError" in output:
                return True
            else:
                return False

    def test_json_logger_with_exception(self):
        try:
            out = io.StringIO()
            LOGGER = Logger().get_logger(json=True)
            a = 100
            b = 0
            c = a/b
        except Exception as e:
            LOGGER.error("Exception has occured", exc_info=True)
            output = out.getvalue().strip()
            if "exc_info" in output:
                return True
            else:
                return False


if __name__ == "__main__":
    unittest.main()
