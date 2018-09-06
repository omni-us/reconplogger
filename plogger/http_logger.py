import logging.config
import logmatic
from plogger.conf import LOGGING_APPLICATION_CONF
import os

custom_log_adapters = {'http_endpoint': '', 'http_method': '', 'upstream_service': '', 'http_response_code': '',
                       'http_response_size': '', 'http_input_file_size': '', 'http_input_file_type': '',
                       'http_response_time': '', 'client_ip': '', 'hostname': '', 'user-agent': ''}


class HTTP_Logger:
    '''
    Class to support HTTP Logger for python applications
    '''

    def __init__(self):
        '''This method sets the configuration for the logger
        Returns:
            [HTTP_LOGGER] --  An instance of Logging with the right handlers set
        '''

        logging.config.dictConfig(LOGGING_APPLICATION_CONF)
        logger = logging.getLogger("http")
        handlers = logger.handlers
        logger.handlers = []
        logger.addHandler(handlers[0])
        self.logger = logger

    def info(self, uuid, http_endpoint, http_method,
             http_response_code, http_response_size, http_input_payload_size,
             http_input_payload_type, http_response_time, message, hostname, exception):
        '''[summary]

        Arguments:
            uuid {String} -- UUID sent in the request
            http_endpoint {String} -- [description]
            http_method {String} -- [description]
            http_response_code {String} -- [description]
            http_response_size {String} -- [description]
            http_input_payload_size {String} -- [description]
            http_input_payload_type {String} -- [description]
            http_response_time {String} -- [description]
            message {String} -- [description]
            hostname {String} -- [description]
            exception {Exception} - Exception object
        '''
        if exception is not None:
            self.logger.info(message, extra={'uuid': uuid, 'http_endpoint': http_endpoint, 'http_method': http_method,
                                            'http_response_code': http_response_code, 'http_response_size': http_response_size,
                                            'http_input_payload_size': http_input_payload_size,
                                            'http_input_payload_type': http_input_payload_type, 'http_response_time': http_response_time, 'hostname': hostname}, 
                                            exc_info=True)
        else:
            self.logger.info(message, extra={'uuid': uuid, 'http_endpoint': http_endpoint, 'http_method': http_method,
                                            'http_response_code': http_response_code, 'http_response_size': http_response_size,
                                            'http_input_payload_size': http_input_payload_size,
                                            'http_input_payload_type': http_input_payload_type, 'http_response_time': http_response_time, 'hostname': hostname})

