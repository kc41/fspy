import logging
import weakref

from aiohttp import web, WSCloseCode

from fspy.collector import view
from fspy.collector.utils import AppWrapper
from fspy.collector.writing_thread import WriteThreadManager

log = logging.getLogger(__name__)


async def on_shutdown(app: web.Application):
    app_wrapper = AppWrapper(app)

    log.info("Closing web-sockets")
    for ws in set(app_wrapper.web_sockets):
        await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')

    await app_wrapper.writing_thread_manager.close()

    log.info("On shutdown procedure finished")


def create_application():
    log.info("Creating WSLC application")
    app = web.Application()

    app_wrapper = AppWrapper(app)

    app_wrapper.web_sockets = weakref.WeakSet()
    app_wrapper.writing_thread_manager = WriteThreadManager(loop=app.loop)

    log.info("Adding routes")
    app.add_routes([
        web.view("/ws", view.LogsCollectorView),
    ])

    app.on_shutdown.append(on_shutdown)

    app_wrapper.writing_thread_manager.run_worker()

    return app
