import logging
from aiohttp import web

import pydantic
import json

from fspy.collector.utils import AppWrapper
from fspy.common.model import DiffReportHandlingResponse, DiffReport

log = logging.getLogger(__name__)


class LogsCollectorView(web.View):

    @staticmethod
    def _get_resp_dict(handled=True, message=None):
        return DiffReportHandlingResponse(handled=handled, message=message).dict()

    async def get(self):
        app_w = AppWrapper(self.request.app)

        log.info(f"Handling new WS connection from {self.request.remote}")
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        app_w.web_sockets.add(ws)

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        msg_dict = json.loads(msg.data)
                        diff_report = DiffReport(**msg_dict)
                    except json.JSONDecodeError:
                        log.warning(f"Can not decode message from {self.request.remote}: {msg.data}")

                        await ws.send_json(self._get_resp_dict(handled=False, message="Malformed JSON"))
                        continue
                    except pydantic.ValidationError as e:
                        log.warning(f"Malformed message schema in message from {self.request.remote}: {e}")

                        await ws.send_json(self._get_resp_dict(handled=False, message=str(e)))
                        continue

                    # TODO FIX: Improve verbosity
                    log.info(f"Diff report from {diff_report}")

                    # noinspection PyBroadException
                    try:
                        await app_w.writing_thread_manager.save(msg.data)
                        await ws.send_json(self._get_resp_dict(handled=True))

                    except Exception:
                        log.exception(f"Error during saving diff report from {self.request.remote}")
                        await ws.send_json(self._get_resp_dict(handled=False, message="Unexpected error"))
                else:
                    log.warning(f"Unexpected message type from {self.request.remote}: {msg.type}")
                    await ws.send_json(self._get_resp_dict(handled=False, message="Unknown message type"))
        finally:
            app_w.web_sockets.discard(ws)

        return ws
