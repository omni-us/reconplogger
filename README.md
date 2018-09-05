## Plogger - omnius python logger

This repository contains code of a standard python logging library with standard template to be used across experiments and services.
Repository supports:

* Application Logging

* HTTP logging

### Install from internal pypi repository
```pip install plogger --trusted-host 35.189.220.104```

## How to use

In the ```___init__.py``` of your project create an instance of the plogger as following:
``` 
    from plogger.logger import Logger

    logger = Logger().get_logger() // if you do not require logs to be pushed as json
    logger = Logger().get_logger(json=True) // if you want the logs to be pushed as json
```


### Currently Support

* Application logs

Application logs in JSON format:
```
{"asctime": "2018-09-05 17:38:38,137", "levelname": "INFO", "filename": "test_formatter.py", "lineno": 5, "message": "Hello world"}
{"asctime": "2018-09-05 17:38:38,137", "levelname": "DEBUG", "filename": "test_formatter.py", "lineno": 9, "message": "Hello world"}
{"asctime": "2018-09-05 17:38:38,137", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 13, "message": "Hello world"}
{"asctime": "2018-09-05 17:38:38,137", "levelname": "CRITICAL", "filename": "test_formatter.py", "lineno": 17, "message": "Hello world"}
{"asctime": "2018-09-05 17:38:38,137", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 25, "message": "division by zero"}
{"asctime": "2018-09-05 17:38:38,138", "levelname": "ERROR", "filename": "test_formatter.py", "lineno": 33, "message": "Exception has occured", "exc_info": "Traceback (most recent call last):\n  File \"plogger/tests/test_formatter.py\", line 31, in test_exception_with_trace\n    b = 100 / 0\nZeroDivisionError: division by zero"}
{"asctime": "2018-09-05 17:38:38,138", "levelname": "INFO", "filename": "test_formatter.py", "lineno": 37, "message": "Hello world", "context check": "check"}
```

Application logs in standard out format:
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

### Coming soon

* HTTP Logs


