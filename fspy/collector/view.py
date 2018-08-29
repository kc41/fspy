import logging
from aiohttp import web

from fspy.collector.utils import AppWrapper

log = logging.getLogger(__name__)


class LogsCollectorView(web.View):

    async def get(self):
        app_w = AppWrapper(self.request.app)

        log.info(f"Handling new WS connection from {self.request.remote}")
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        app_w.web_sockets.add(ws)

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    log.info(f"Text message from {self.request.remote}: {msg.data}")

                    result = await app_w.writing_thread_manager.save(msg.data)
                    await ws.send_str(result)
                else:
                    log.warning(f"Other message from {self.request.remote}: {msg}")
        finally:
            app_w.web_sockets.discard(ws)

        return ws
