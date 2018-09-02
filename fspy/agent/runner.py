import asyncio

import logging
import logging.config

from fspy.agent.scanner import SimpleComparator
from fspy.agent.sender import DiffSender
from fspy.common import model

log = logging.getLogger(__name__)


def log_full_diff(full_diff: model.FullDiff):
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
        self._diff_queue = asyncio.Queue(loop=loop)
        self._launch_delay = 2

        self._scanner = SimpleComparator(scan_target)
        self._diff_sender = DiffSender(ws_url=ws_url, diff_queue=self._diff_queue, loop=loop)

    # TODO FIX: use single thread executor to totally prevent parallel launches of SimpleComparator
    async def _collect_diff(self):
        # noinspection PyBroadException
        try:
            log.debug("Running directory scan")
            full_diff = await self._loop.run_in_executor(None, self._scanner.scan)
            log.debug("Directory scan finished")

            if full_diff:
                log.info(f"FS changes detected "
                         f"created: {len(full_diff.created)} "
                         f"deleted: {len(full_diff.deleted)} "
                         f"updated: {len(full_diff.updated)}")
                log_full_diff(full_diff)

                await self._diff_queue.put(full_diff)
            else:
                log.debug("No FS changes was detected")

        except Exception:
            log.exception("Exception during diff collection")

    async def close(self):
        await self._diff_sender.close()

    async def run(self):
        log.info("Running diff sender")
        await self._diff_sender.run()

        log.info("Starting infinite directory scanning")
        while True:
            await self._collect_diff()
            await asyncio.sleep(self._launch_delay)


def main(scan_target: str, ws_url: str):
    loop = asyncio.get_event_loop()

    log.info(f"Client app start. Scan directory: {scan_target}. Server WS URL: {ws_url}")

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
