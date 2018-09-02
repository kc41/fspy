import logging
import weakref

from aiohttp import web, WSCloseCode
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy import pool
import asyncio

from fspy.collector import view
from fspy.collector.db import Base
from fspy.collector.terminal import diff_report_printer
from fspy.collector.utils import AppWrapper
from fspy.collector.writing_thread import WriteThreadManager

log = logging.getLogger(__name__)


def run_migrations(engine: Engine):
    log.info("Running migrations")
    # TODO FIX: Replace with running Alembic migrations
    Base.metadata.create_all(engine)


async def on_shutdown(app: web.Application):
    app_wrapper = AppWrapper(app)

    log.info("Closing web-sockets")
    for ws in set(app_wrapper.web_sockets):
        await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')

    await app_wrapper.writing_thread_manager.close()

    app_wrapper.terminal_task.cancel()

    log.info("On shutdown procedure finished")


async def on_startup(app: web.Application):
    log.info("Running FSPY startup procedure")

    app_wrapper = AppWrapper(app)

    log.info("Creating DB engine")

    app_wrapper.db_engine = create_engine(f"sqlite:///{app_wrapper.db_path}", poolclass=pool.SingletonThreadPool)

    await app.loop.run_in_executor(None, run_migrations, app_wrapper.db_engine)

    log.info("Running writing thread")
    app_wrapper.writing_thread_manager.run_worker(app_wrapper.db_engine)

    log.info("Initiating terminal task")
    app_wrapper.terminal_queue = asyncio.Queue()
    app_wrapper.terminal_task = asyncio.ensure_future(diff_report_printer(app_wrapper.terminal_queue), loop=app.loop)

    log.info("FSPY startup procedure finished")


def create_application(db_path: str):
    log.info("Creating FSPY application")
    app = web.Application()

    app_wrapper = AppWrapper(app)

    app_wrapper.db_path = db_path
    app_wrapper.web_sockets = weakref.WeakSet()
    app_wrapper.writing_thread_manager = WriteThreadManager(loop=app.loop)

    log.info("Adding routes")
    app.add_routes([
        web.view("/ws", view.LogsCollectorView),
        web.view("/flat_report", view.FlatReportView),
    ])

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app
