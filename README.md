## Plogger - omnius python logger

This repository contains code of a standard python logging library with standard template to be used across experiments and services.
Repository supports:

* Application Logging

* HTTP logging

### Install from internal pypi repository
```pip install plogger --trusted-host 35.189.220.104```

# Application Logger

## How to use :

In the ```___init__.py``` of your project create an instance of the plogger application logger as following:
``` 
    from plogger.logger import Logger

    logger = Logger().get_logger() // if you do not require logs to be pushed as json
    logger = Logger().get_logger(json=True) // if you want the logs to be pushed as json
```



**Application logs in JSON format**:
```
{"asctime": "2018-09-05 17:38:38,137", "levelname": "INFO", "filename": "test_formatter.py", "lineno": 5, "message": "Hello world"}
{"asctime": "2018-09-05 17:38:38,137", "levelname": "DEBUG", "filename": "test_formatter.py", "lineno": 9, "message": "Hello world"}
{"asctime": "2018-09-05 17:38:38,137", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 13, "message": "Hello world"}
{"asctime": "2018-09-05 17:38:38,137", "levelname": "CRITICAL", "filename": "test_formatter.py", "lineno": 17, "message": "Hello world"}
{"asctime": "2018-09-05 17:38:38,137", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 25, "message": "division by zero"}
{"asctime": "2018-09-05 17:38:38,138", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 33, "message": "Exception has occured", "exc_info": "Traceback (most recent call last):\n  File \"plogger/tests/test_formatter.py\", line 31, in test_exception_with_trace\n    b = 100 / 0\nZeroDivisionError: division by zero"}
{"asctime": "2018-09-05 17:38:38,138", "levelname": "INFO", "filename": "test_formatter.py", "lineno": 37, "message": "Hello world", "context check": "check"}
```

**Application logs in standard out format**:
```
2018-09-05 17:38:38,136 INFO -- test_formatter.py:5 -- Hello world
2018-09-05 17:38:38,136 DEBUG -- test_formatter.py:9 -- Hello world
2018-09-05 17:38:38,136 ERROR -- test_formatter.py:13 -- Hello world
2018-09-05 17:38:38,137 CRITICAL -- test_formatter.py:17 -- Hello world
2018-09-05 17:38:38,137 ERROR -- test_formatter.py:25 -- division by zero
2018-09-05 17:38:38,137 ERROR -- test_formatter.py:33 -- Exception has occured
Traceback (most recent call last):
  File "plogger/tests/test_formatter.py", line 31, in test_exception_with_trace
    b = 100 / 0
ZeroDivisionError: division by zero

```

# HTTP Logger

## How to use


In the ```___init__.py``` of your project create an instance of the plogger http logger as following:
``` 
from plogger.http_logger import HTTP_Logger

logger = HTTP_Logger() // instatiate an instance of HTTP logger

'''
use the info method of the HTTP logger
if http method call is success use exception parameter as None
'''

logger.info(uuid='abcabcbabca', http_endpoint='/home',
            http_response_code='200', http_method='add_module', http_response_size='1.5kb', http_input_payload_size='1mb',
            http_input_payload_type='file', http_response_time='10ms', message="Testing HTTP Logger", hostname='local', exception=None) 

'''
if http method call is failure pass the exception object as parameter
'''

try:
    a = 100
    b = 0
    c = a/b
except Exception as e:
    logger.info(uuid='abcabcbabca', http_endpoint='/home',
                http_response_code='200', http_method='add_module', http_response_size='1.5kb', http_input_payload_size='1mb',
                http_input_payload_type='file', http_response_time='10ms', message="Testing HTTP Logger", hostname='local', exception=e)
```

**HTTP Logs in JSON format**:

```
# Without exception
{"asctime": "2018-09-06 15:43:53,763", "levelname": "INFO", "filename": "http_logger.py", "lineno": 57, "message": "Testing HTTP Logger", "uuid": "abcabcbabca", "http_endpoint": "/home", "http_method": "add_module", "http_response_code": "200", "http_response_size": "1.5kb", "http_input_payload_size": "1mb", "http_input_payload_type": "file", "http_response_time": "10ms", "hostname": "local"}

# With exception
{"asctime": "2018-09-06 15:43:53,764", "levelname": "INFO", "filename": "http_logger.py", "lineno": 52, "message": "Testing HTTP Logger", "exc_info": "Traceback (most recent call last):\n  File \"plogger/tests/test_http_logs.py\", line 16, in <module>\n    c = a/b\nZeroDivisionError: division by zero", "uuid": "abcabcbabca", "http_endpoint": "/home", "http_method": "add_module", "http_response_code": "500", "http_response_size": "1.5kb", "http_input_payload_size": "1mb", "http_input_payload_type": "file", "http_response_time": "10ms", "hostname": "local"}
```