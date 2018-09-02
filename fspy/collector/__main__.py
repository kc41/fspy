import logging
import asyncio

from argparse import ArgumentParser
from aiohttp import web

from fspy.collector.app import create_application
from fspy.collector import logging_config
from fspy.common import defaults

log = logging.getLogger(__name__)


async def init_app(host: str, port: int, db_path: str) -> web.AppRunner:
    app = create_application(db_path=db_path)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    return runner


def main():
    parser = ArgumentParser(description="File System Spy collector server")

    parser.add_argument("--host", default="0.0.0.0", help="bind address")
    parser.add_argument("--port", default=defaults.DEFAULT_PORT, type=int, help="bind port")
    parser.add_argument("--db_path", help="Path to SQLite DB. If does not exists - will be created", required=True)

    args = parser.parse_args()

    logging_config.init_logging()

    log.info(f"Running FSPY server at {args.host}:{args.port}. DB path is: {args.db_path}")

    log.info(f"Preparing HTTP server")

    loop = asyncio.get_event_loop()
    runner = loop.run_until_complete(init_app(args.host, args.port, args.db_path))

    try:
        log.info(f"Running main event loop forever")
        loop.run_forever()
    except KeyboardInterrupt:
        log.info("Interrupt signal received")
        loop.run_until_complete(runner.cleanup())


if __name__ == '__main__':
    main()
