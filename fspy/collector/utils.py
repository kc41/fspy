from typing import Type
import weakref

import logging

from functools import wraps
from pydantic import BaseModel

from aiohttp import web
from sqlalchemy.engine import Engine

from fspy.collector.writing_thread import WriteThreadManager
import asyncio

log = logging.getLogger(__name__)


class AppWrapper:
    __slots__ = '_app'

    KEY_WEB_SOCKETS = "web_sockets"
    KEY_WRITE_THREAD_MANAGER = "write_thread_manager"
    KEY_DB_ENGINE = "db_engine"
    KEY_DB_PATH = "db_path"
    KEY_TERMINAL_TASK = "terminal_task"
    KEY_TERMINAL_QUEUE = "terminal_queue"

    def __init__(self, app: web.Application):
        self._app = app

    @property
    def web_sockets(self) -> weakref.WeakSet:
        return self._app[self.KEY_WEB_SOCKETS]

    @web_sockets.setter
    def web_sockets(self, val):
        self._app[self.KEY_WEB_SOCKETS] = val

    @property
    def writing_thread_manager(self) -> WriteThreadManager:
        return self._app[self.KEY_WRITE_THREAD_MANAGER]

    @writing_thread_manager.setter
    def writing_thread_manager(self, val):
        self._app[self.KEY_WRITE_THREAD_MANAGER] = val

    @property
    def db_engine(self) -> Engine:
        return self._app[self.KEY_DB_ENGINE]

    @db_engine.setter
    def db_engine(self, val: Engine):
        self._app[self.KEY_DB_ENGINE] = val

    @property
    def db_path(self) -> str:
        return self._app[self.KEY_DB_PATH]

    @db_path.setter
    def db_path(self, val: str):
        self._app[self.KEY_DB_PATH] = val

    @property
    def terminal_task(self) -> asyncio.Task:
        return self._app[self.KEY_TERMINAL_TASK]

    @terminal_task.setter
    def terminal_task(self, val: asyncio.Task):
        self._app[self.KEY_TERMINAL_TASK] = val

    @property
    def terminal_queue(self) -> asyncio.Queue:
        return self._app[self.KEY_TERMINAL_QUEUE]

    @terminal_queue.setter
    def terminal_queue(self, val: asyncio.Queue):
        self._app[self.KEY_TERMINAL_QUEUE] = val


def marshal_response(*types: Type[BaseModel]):
    def wrapper(fn):
        @wraps(fn)
        async def wrapped(*args, **kwargs):
            log.debug("Marshal wrapper launched")

            result = await fn(*args, **kwargs)  # type: BaseModel

            log.debug("Handler %s returns object with type %s", fn, type(result))

            if types:
                if not isinstance(result, tuple(types)):
                    log.error(f"Handler {fn} returns unexpected type {type(result)}. Expected: [{args}]")
                    return web.Response(status=500)

            else:
                if not isinstance(result, BaseModel):
                    log.error(
                        f"Handler {fn} returns unexpected type {type(result)}. Expected: subclass if pydantic.BaseModel")
                    return web.Response(status=500)

            return web.json_response(result.dict())

        return wrapped

    return wrapper
