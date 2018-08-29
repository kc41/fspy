import asyncio

import logging
import logging.config

from fspy.agent.scanner import SimpleComparator
from fspy.common.model import FullDiff
from fspy.common_logging import LOG_FMT

log = logging.getLogger(__name__)


def log_full_diff(full_diff: FullDiff):
    if log.isEnabledFor(logging.DEBUG) and full_diff:
        for fs in full_diff.created:
            log.debug("File was created: %s", fs)
        for fs in full_diff.deleted:
            log.debug("File was deleted: %s", fs)
        for fds in full_diff.updated:
            log.debug("File was updated: %s", fds)


async def main_coro(scanner: SimpleComparator):
    while True:
        # noinspection PyBroadException
        try:
            log.info("Running directory scan")
            full_diff = scanner.scan()
            log.info("Directory scan finished")

            if full_diff:
                log.info(f"FS changes detected " 
                         f"created: {len(full_diff.created)} "
                         f"deleted: {len(full_diff.deleted)} "
                         f"updated: {len(full_diff.updated)}")
                log_full_diff(full_diff)
            else:
                log.info("No FS changes was detected")
        except Exception:
            log.exception("Exception in main cycle")

        await asyncio.sleep(2)


def main():
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
            }
        },
    })

    loop = asyncio.get_event_loop()

    log.info("Client app start")
    try:
        loop.run_until_complete(main_coro(
            scanner=SimpleComparator(".")
        ))
    except KeyboardInterrupt:
        pass
    finally:
        log.info("Client app stop")
        loop.close()
