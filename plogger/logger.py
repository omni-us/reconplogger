import logging.config
import logmatic
from plogger.conf import LOGGING_APPLICATION_CONF

custom_log_adapters = {'http_endpoint': '', 'http_method': '', 'upstream_service': '', 'http_response_code': '',
                       'http_response_size': '', 'http_input_file_size': '', 'http_input_file_type': '',
                       'http_response_time': '', 'client_ip': '', 'hostname': '', 'user-agent': ''}


class Logger:
    '''    
    This class contains methods to use standard loggers
    '''

    def get_logger(self, json=False):
        '''This method sets the configuration for the logger
        
        Keyword Arguments:
            json {bool} -- If the logger should convert the logs into json format (default: {False})
        
        Returns:
            [Logger] --  An instance of Logging with the right handlers set
        '''

        logging.config.dictConfig(LOGGING_APPLICATION_CONF)
        logger = logging.getLogger()
        handlers = logger.handlers
        if json:
            handler = logging.StreamHandler()
            logger.handlers = []
            logger.addHandler(handlers[0])
        else:
            handler = logging.StreamHandler()
            logger.handlers = []
            logger.addHandler(handlers[1])
        return logger
