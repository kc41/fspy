import unittest

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from fspy.collector.logging import init_logging
from fspy.collector.app import create_application


class CollectorBaseTests(AioHTTPTestCase):
    async def get_application(self):
        init_logging()
        return create_application()

    @unittest_run_loop
    async def test_connect_to_logging_ws(self):
        msg_count = 10

        async with self.client.ws_connect("/ws") as ws:
            for i in range(0, msg_count):
                await ws.send_str(f"M{i}")
                await ws.receive()


if __name__ == '__main__':
    unittest.main()
