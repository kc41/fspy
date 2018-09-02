from typing import Optional, List

import logging

import pytz
from aiohttp import web

import pydantic
import json

from datetime import datetime
import tzlocal

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from fspy.collector import db, schemas
from fspy.collector.utils import AppWrapper
from fspy.common.model import DiffReportHandlingResponse, DiffReport, FullDiff

log = logging.getLogger(__name__)


# noinspection PyUnresolvedReferences
class GetArgsMixin:
    def parse_arg(self):
        try:
            return self.GetArgs(**dict(self.request.rel_url.query))
        except pydantic.ValidationError as e:
            raise web.HTTPBadRequest(content_type='application/json', body=e.json())


class LogsCollectorView(web.View, GetArgsMixin):
    class GetArgs(pydantic.BaseModel):
        source_name: str

    @staticmethod
    def _get_resp_dict(handled=True, message=None):
        return DiffReportHandlingResponse(handled=handled, message=message).dict()

    async def get(self):
        args = self.parse_arg()  # type: self.GetArgs

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
                        diff_report = DiffReport(
                            source_name=args.source_name,
                            diff=FullDiff(**msg_dict)
                        )
                    except json.JSONDecodeError:
                        log.warning(f"Can not decode message from {self.request.remote}: {msg.data}")

                        await ws.send_json(self._get_resp_dict(handled=False, message="Malformed JSON"))
                        continue
                    except pydantic.ValidationError as e:
                        log.warning(f"Malformed message schema in message from {self.request.remote}: {e}")

                        await ws.send_json(self._get_resp_dict(handled=False, message=str(e)))
                        continue

                    log.info(f"Diff report from {self.request.remote}/{diff_report.source_name}")

                    # noinspection PyBroadException
                    try:
                        app_w.terminal_queue.put_nowait(diff_report)
                        await app_w.writing_thread_manager.save(diff_report, source_ip=self.request.remote)
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


class FlatReportView(web.View, GetArgsMixin):
    class GetArgs(pydantic.BaseModel):
        date_start: datetime
        date_end: datetime
        source: Optional[str] = None

        # noinspection PyMethodParameters
        @pydantic.validator("date_start", "date_end")
        def set_timezone(cls, value: datetime):
            if value.tzinfo is None:
                value = tzlocal.get_localzone().localize(value)
            return value

    def sync_get(self, args: "GetArgs"):
        app_w = AppWrapper(self.request.app)
        session = Session(bind=app_w.db_engine)

        query = session.query(db.FileDiff).options(
            joinedload(db.FileDiff.diff_report)
        ).join(
            db.FileDiff.diff_report
        ).filter(
            and_(
                db.FileDiff.operation_time <= args.date_end.astimezone(pytz.utc),
                db.FileDiff.operation_time >= args.date_start.astimezone(pytz.utc)
            )
        )

        if args.source:
            query = query.filter(
                db.DiffReport.source_name == args.source
            )

        query = query.order_by(
            db.FileDiff.operation_time
        )

        result = query.all()  # type: List[db.FileDiff]

        session.close()

        return schemas.FlatReportSchema(
            entries=[
                schemas.FlatReportEntrySchema(
                    source_name=file_diff.diff_report.source_name,
                    source_ip=file_diff.diff_report.source_ip,

                    file_path=file_diff.file_path,
                    operation=file_diff.operation,

                    size_before=file_diff.size_before,
                    size_after=file_diff.size_after,

                    operation_time=file_diff.operation_time,
                )
                for file_diff in result
            ]
        )

    async def get(self):
        args = self.parse_arg()  # type: self.GetArgs

        loop = self.request.app.loop

        # TODO FIX: Use explicit thread pool executor
        report = await loop.run_in_executor(None, self.sync_get, args)

        return web.json_response(text=report.json())
