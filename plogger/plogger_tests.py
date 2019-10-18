import unittest
import plogger
from testfixtures import LogCapture, compare, Comparison


class TestPlogger(unittest.TestCase):
    def test_default_logger(self):
        logging = plogger.load_config('plogger_default')
        logger = logging.getLogger('plogger')
        info_msg = 'Hello World'
        with LogCapture() as log:
            logger.info(info_msg)
            log.check( ('plogger', 'INFO', info_msg) )

    def test_default_logger_with_exception(self):
        logging = plogger.load_config('plogger_default')
        logger = logging.getLogger('plogger')
        error_msg = 'Error message'
        exception = RuntimeError('Exception message')
        with LogCapture() as log:
            try:
                raise exception
            except:
                logger.error(error_msg, exc_info=True)
                compare(Comparison(exception), log.records[-1].exc_info[1])
                log.check( ('plogger', 'ERROR', error_msg) )


if __name__ == "__main__":
    unittest.main(verbosity=2)
