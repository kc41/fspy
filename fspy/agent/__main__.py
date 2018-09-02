from os import path
from fspy.agent import runner
from fspy.common import defaults

import logging.config

import argparse

from fspy.common.logging_config import LOG_FMT


def main():
    parser = argparse.ArgumentParser("FSPY client")
    parser.add_argument("--target", type=str, help="Directory to scan", required=True)
    parser.add_argument("--source_name", type=str, help="Name of this FSPY client instance", required=True)
    parser.add_argument("--server_host", type=str, help="FSPY server hostname/IP", default="127.0.0.1")
    parser.add_argument("--server_port", type=int, help="FSPY server port", default=defaults.DEFAULT_PORT)

    args = parser.parse_args()

    ws_url = f"ws://{args.server_host}:{args.server_port}/ws?source_name={args.source_name}"
    target = path.abspath(args.target)

    if not path.isdir(target):
        print(f"{target} is not a directory")

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
            '__main__': {
                'level': 'INFO',
            },
            'fspy.agent.runner': {
                'level': 'INFO',
            },
            'fspy.agent.scanner': {
                'level': 'INFO',
            },
            'fspy.agent.sender': {
                'level': 'INFO',
            }
        },
    })

    runner.main(ws_url=ws_url, scan_target=target)


if __name__ == '__main__':
    main()
