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


def _finish_future(fut: asyncio.Future, result: Any):
    fut.set_result(result)


def _finish_future_with_exc(fut: asyncio.Future, exc: Exception):
    fut.set_exception(exc)


def _serve_write_queue(q: Queue):
    while True:
        # noinspection PyBroadException
        try:
            log.debug("Waiting for task in queue")
            task = q.get()  # type: Optional[WriteTask]
            log.debug(f"Task fetched from queue {task}")

            if task is None:
                log.debug("Empty task received. Exiting...")
                break

            try:
                time.sleep(1)
            except Exception as exc:
                task.loop.call_soon_threadsafe(_finish_future_with_exc, task.future, exc)
                continue

            task.loop.call_soon_threadsafe(_finish_future, task.future, None)

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
        log.debug("Get result from worker thread for %s", result)

        return result

    async def close(self) -> None:
        log.info("Sending stop signal to working thread")
        await self.task_queue.async_q.put(None)
        log.info("Waiting for working thread to stop")

        # TODO FIX: do not lock main loop!!!
        self.worker_thread.join()
