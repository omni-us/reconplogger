from plogger.http_logger import HTTP_Logger
from plogger.logger import Logger

logger = HTTP_Logger()
app_logger = Logger().get_logger()

app_logger.info("Testing http logger without exception")
logger.info(uuid='abcabcbabca', http_endpoint='/home',
            http_response_code='200', http_method='add_module', http_response_size='1.5kb', http_input_payload_size='1mb',
            http_input_payload_type='file', http_response_time='10ms', message="Testing HTTP Logger", hostname='local', exception=None)

try:
    app_logger.info("Testing http logger with exception")
    a = 100
    b = 0
    c = a/b
except Exception as e:
    logger.info(uuid='abcabcbabca', http_endpoint='/home',
                http_response_code='200', http_method='add_module', http_response_size='1.5kb', http_input_payload_size='1mb',
                http_input_payload_type='file', http_response_time='10ms', message="Testing HTTP Logger", hostname='local', exception=e)