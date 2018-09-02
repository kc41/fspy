from typing import Optional

import asyncio
import aiohttp

import logging

from fspy.common import model

log = logging.getLogger(__name__)


class DiffSender:
    def __init__(self, ws_url: str, diff_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self._loop = loop

        self._ws_url = ws_url
        self._ws = None
        self._session = aiohttp.ClientSession(loop=loop)

        self._diff_send_task = None  # type: asyncio.Task
        self._diff_queue = diff_queue

    async def _get_ws(self) -> Optional[aiohttp.ClientWebSocketResponse]:
        if self._ws is None or self._ws.closed:
            log.info("Connecting to web-socket")
            self._ws = None
            # noinspection PyBroadException
            try:
                self._ws = await self._session.ws_connect(self._ws_url)
                log.info("Web-socket connection established")
            except Exception:
                log.exception("Failed to connect to web-socket")
                return None

        return self._ws

    async def _send_diff_attempt(self, diff: model.FullDiff) -> bool:
        ws = await self._get_ws()

        if ws is None:
            log.warning("Can not get WS. Waiting for next attempt")
            return False

        # noinspection PyBroadException
        try:
            await ws.send_str(diff.json())
            resp_dict = await ws.receive_json()
            resp = model.DiffReportHandlingResponse(**resp_dict)

            if not resp.handled:
                log.error(f"Server did not handle diff. Message: '{resp.message}'. Waiting for next attempt")
                return False

        except Exception:
            log.exception("Error during sending diff report. Waiting for next attempt")
            return False

        return True

    async def _send_diff(self, diff, max_attempts=10, attempts_delay=5) -> bool:

        for attempt_num in range(1, max_attempts + 1):
            log.debug(f"Trying to send diff (attempt {attempt_num} of {max_attempts})")
            success = await self._send_diff_attempt(diff)
            if success:
                log.debug(f"Diff successfully sent to server")
                return True

            if attempt_num != max_attempts:
                await asyncio.sleep(attempts_delay)

        log.warning("Max number of attempts was exceeded. This diff will not be sent.")
        return False

    async def _serve_diff_queue(self):
        # Initial attempt to connect
        await self._get_ws()

        while True:
            log.debug("Awaiting next diff in queue")
            next_diff = await self._diff_queue.get()

            log.debug("Diff received from queue")
            await self._send_diff(next_diff)

    async def close(self):
        if self._ws:
            await self._ws.close()

        if self._diff_send_task:
            self._diff_send_task.cancel()

        await self._session.close()

    async def run(self):
        log.info("Running diff send task")
        self._diff_send_task = asyncio.ensure_future(self._serve_diff_queue(), loop=self._loop)
