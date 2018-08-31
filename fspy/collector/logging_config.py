import logging
import logging.config

from fspy.common_logging import LOG_FMT


def init_logging(log_sql=False):
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'class': 'logging.Formatter',
                'format': LOG_FMT
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default'
            },
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'INFO',
            },
            'fspy.agent.runner': {
                'level': 'DEBUG',
            },
            'sqlalchemy.engine': {
                'level': 'INFO' if log_sql else 'WARNING'
            }
        },
    })
