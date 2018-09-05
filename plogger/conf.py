LOGGING_APPLICATION_CONF = {
    'version': 1,  # required
    'disable_existing_loggers': True,  # this config overrides all other loggers
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s -- %(message)s'
        },
        'sysout': {
            'format': '%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s',

        },
        'json': {
            'format': '%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s',
            'class': 'logmatic.jsonlogger.JsonFormatter'
        }
    },
    'handlers': {
        'json': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'sysout'
        }
    },
    'loggers': {
        '': {  # 'root' logge
            'level': 'DEBUG',
            'handlers': ['json', 'console']
        }
    }
}
