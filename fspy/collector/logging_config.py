import logging
import logging.config

from fspy.common.logging_config import LOG_FMT


def init_logging(log_sql=False, terminal_only=True):
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

            'sqlalchemy.engine': {
                'level': 'INFO' if log_sql else 'WARNING'
            },

            'aiohttp.access': {
                'level': 'WARNING' if terminal_only else 'INFO',
            },
            'aiohttp.server': {
                'level': 'WARNING' if terminal_only else 'INFO',
            },

            '__main__': {
                'level': 'INFO',
            },

            'fspy.collector': {
                'level': 'WARNING' if terminal_only else 'INFO',
            },
            'fspy.collector.app': {
                'level': 'INFO',
            },
            'fspy.collector.views': {
                'level': 'WARNING' if terminal_only else 'INFO',
            },
            'fspy.collector.writing_thread': {
                'level': 'WARNING' if terminal_only else 'INFO',
            },

            'fspy.collector.terminal': {
                'level': 'INFO' if terminal_only else 'WARNING',
                'propagate': terminal_only,
            },
        },
    })
