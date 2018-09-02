from typing import Optional

import asyncio
import aiohttp

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


class Agent:
    def __init__(self, ws_url: str, scan_target: str, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._scanner = SimpleComparator(scan_target)

        self._ws_url = ws_url
        self._ws = None
        self._session = aiohttp.ClientSession(loop=loop)

        self._diff_send_task = None  # type: asyncio.Task
        self._diff_queue = asyncio.Queue(loop=loop)

        self._launch_delay = 2

    async def _get_ws(self) -> Optional[aiohttp.ClientWebSocketResponse]:
        if self._ws is None:
            log.info("Connecting to web-socket")
            # noinspection PyBroadException
            try:
                self._ws = await self._session.ws_connect(self._ws_url)
            except Exception:
                log.exception("Failed to connect to web-socket")
                return None

        return self._ws

    async def _send_diff_attempt(self, diff) -> bool:
        ws = await self._get_ws()

        if ws is None:
            log.warning("Can not get WS. Waiting for next attempt")
            return False

        # TODO FIX: send diff
        return True

    async def _send_diff(self, diff, max_attempts=3, attempts_delay=5) -> bool:

        for attempt_num in range(0, max_attempts):
            success = await self._send_diff_attempt(diff)
            if success:
                return True

            await asyncio.sleep(attempts_delay)

        return False

    async def _serve_diff_queue(self):
        while True:
            log.debug("Awaiting next diff in queue")
            next_diff = await self._diff_queue.get()

            log.debug("Diff received from queue")
            await self._send_diff(next_diff)

    # TODO FIX: use single thread executor to totally prevent parallel launches of SimpleComparator
    async def _collect_diff(self):
        # noinspection PyBroadException
        try:
            log.info("Running directory scan")
            full_diff = await self._loop.run_in_executor(None, self._scanner.scan)
            log.info("Directory scan finished")

            if full_diff:
                log.info(f"FS changes detected "
                         f"created: {len(full_diff.created)} "
                         f"deleted: {len(full_diff.deleted)} "
                         f"updated: {len(full_diff.updated)}")
                log_full_diff(full_diff)

                await self._diff_queue.put(full_diff)
            else:
                log.info("No FS changes was detected")

        except Exception:
            log.exception("Exception during diff collection")

    async def close(self):
        if self._ws:
            await self._ws.close()

        if self._diff_send_task:
            self._diff_send_task.cancel()

        await self._session.close()

    async def run(self):
        # Initial attempt to connect
        await self._get_ws()
        log.info("Running diff send task")
        self._diff_send_task = asyncio.ensure_future(self._serve_diff_queue(), loop=self._loop)

        log.info("Starting infinite directory scanning")
        while True:
            await self._collect_diff()
            await asyncio.sleep(self._launch_delay)


def main(scan_target: str, ws_url: str):
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

    agent = Agent(
        ws_url=ws_url,
        scan_target=scan_target,
        loop=loop
    )

    try:
        loop.run_until_complete(agent.run())
    except KeyboardInterrupt:
        pass
    finally:
        log.info("Client app stop")
        loop.run_until_complete(agent.close())
        loop.close()
