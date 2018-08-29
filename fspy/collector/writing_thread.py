from typing import Optional, NamedTuple, Any
import asyncio
import threading
from queue import Queue
import janus

import logging

import time

log = logging.getLogger(__name__)


class WriteTask(NamedTuple):
    loop: asyncio.AbstractEventLoop
    future: asyncio.Future
    data: Any


def _finish_future(fut: asyncio.Future, result):
    log.info("Closing future %s", fut)
    fut.set_result(result)


def _serve_write_queue(q: Queue):
    while True:
        try:
            log.info("Waiting for task in queue")
            task = q.get()  # type: Optional[WriteTask]
            log.info(f"Task fetched from queue {task}")

            if task is None:
                log.info("Empty task received. Exiting...")
                break

            time.sleep(1)

            task.loop.call_soon_threadsafe(_finish_future, task.future, "OLOLO")

        except Exception:
            log.exception("Error during serving writing queue")


class WriteThreadManager:
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.loop = loop if loop else asyncio.get_event_loop()
        self.task_queue = janus.Queue(loop=self.loop)

        self.worker_thread = threading.Thread(target=_serve_write_queue, args=(self.task_queue.sync_q,))

    def run_worker(self):
        self.worker_thread.start()

    async def save(self, data):
        fut = self.loop.create_future()

        task = WriteTask(
            loop=self.loop,
            future=fut,
            data=data,
        )

        await self.task_queue.async_q.put(task)

        result = await fut
        log.info("Get result from worker thread for %s", result)

        return result

    async def close(self) -> None:
        await self.task_queue.async_q.put(None)
        log.info("Waiting for writing thread")

        # TODO FIX: do not lock main loop!!!
        self.worker_thread.join()
