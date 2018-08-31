import unittest
import tempfile
from os import path, environ

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from fspy.collector.logging_config import init_logging
from fspy.collector.app import create_application
from datetime import datetime
import pytz

from fspy.common.model import DiffReport, FullDiff, DiffReportHandlingResponse, FileState


class CollectorBaseTests(AioHTTPTestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory(prefix="fspy-tests")
        print(self.temp_directory.name)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        if self.temp_directory:
            self.temp_directory.cleanup()

    async def get_application(self):
        init_logging()

        db_path = environ.get(
            "FSPY_TESTS_DB_PATH",
            path.join(self.temp_directory.name, "fspy-tests.sqlite")
        )

        return create_application(db_path)

    @unittest_run_loop
    async def test_connect_to_logging_ws(self):
        msg_count = 10
        # test_start = datetime.now(pytz.utc)

        async with self.client.ws_connect("/ws") as ws:
            for i in range(0, msg_count):
                now = datetime.now(pytz.utc)

                rq = DiffReport(
                    source_name="test_source",
                    diff=FullDiff(
                        run_start=now,
                        run_end=now,
                        deleted=[],
                        created=[
                            FileState(
                                path=f"/var/log/app/{i}.log",
                                date_created=now,
                                date_updated=now,
                                size=512,
                            )
                        ],
                        updated=[],
                    )
                )

                await ws.send_str(rq.json())

                resp_dict = await ws.receive_json()
                resp = DiffReportHandlingResponse(**resp_dict)

                self.assertTrue(resp.handled, f"Diff report was not handled. Message: {resp.message}")


if __name__ == '__main__':
    unittest.main()
