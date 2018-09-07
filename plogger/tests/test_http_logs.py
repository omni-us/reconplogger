import unittest
import io
from plogger.http_logger import HTTP_Logger


class TestHTTPLogger(unittest.TestCase):
    def test_logger(self):
        out = io.StringIO()
        logger = HTTP_Logger()
        logger.info(uuid='abcabcbabca', http_endpoint='/home',
                    http_response_code='200', http_method='add_module', http_response_size='1.5kb', http_input_payload_size='1mb',
                    http_input_payload_type='file', http_response_time='10ms', message="Testing HTTP Logger", hostname='local', exception=None)
        output = out.getvalue().strip()
        if 'http_response_code' in output:
            return True
        else:
            return False
        
    def test_logger_exception(self):
        try:
            out = io.StringIO()
            logger = HTTP_Logger()
            a = 100
            b = 0
            c = a/b
        except Exception as e:
            logger.info(uuid='abcabcbabca', http_endpoint='/home',
                        http_response_code='200', http_method='add_module', http_response_size='1.5kb', http_input_payload_size='1mb',
                        http_input_payload_type='file', http_response_time='10ms', message="Testing HTTP Logger", hostname='local', exception=None)
            output = out.getvalue().strip()
            if 'exc_info' in output:
                return True
            else:
                return False

if __name__ == "__main__":
    unittest.main()