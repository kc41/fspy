from typing import Type
import weakref

import logging

from functools import wraps
from pydantic import BaseModel

from aiohttp import web

from fspy.collector.writing_thread import WriteThreadManager

log = logging.getLogger(__name__)


class AppWrapper:
    __slots__ = '_app'

    KEY_WEB_SOCKETS = "web_sockets"
    KEY_WRITE_THREAD_MANAGER = "write_thread_manager"

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
