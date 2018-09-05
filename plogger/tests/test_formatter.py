from plogger.logger import Logger


def test_info():
    logging.info("Hello world")


def test_debug():
    logging.debug("Hello world")


def test_error():
    logging.error("Hello world")


def test_critical():
    logging.critical("Hello world")


def test_exception():
    try:
        a = 100
        b = 100 / 0
    except Exception as e:
        logging.error(e)


def test_exception_with_trace():
    try:
        a = 100
        b = 100 / 0
    except Exception as e:
        logging.error("Exception has occured", exc_info=True)


def test_logging_with_context():
    logging.info("Hello world", extra={"context check":'check'})


logging = Logger().get_logger()
test_info()
test_debug()
test_error()
test_critical()
test_exception()
test_exception_with_trace()
test_logging_with_context()

logging = Logger().get_logger(json=True)
test_info()
test_debug()
test_error()
test_critical()
test_exception()
test_exception_with_trace()
test_logging_with_context()