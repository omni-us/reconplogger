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

### Coming soon

* HTTP Logs


