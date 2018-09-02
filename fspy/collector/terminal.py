import asyncio
import logging

from datetime import datetime
import tzlocal

from fspy.common.model import DiffReport

log = logging.getLogger(__name__)

TEMPLATE = "{source_name} {operation} {time} {path}"
LOCAL_TZ = tzlocal.get_localzone()


def format_time(time: datetime):
    return time.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")


async def diff_report_printer(diff_report_queue: asyncio.Queue):
    try:
        while True:
            dr = await diff_report_queue.get()  # type: DiffReport
            if log.isEnabledFor(logging.INFO):
                for file_state in dr.diff.created:
                    log.info(TEMPLATE.format(
                        source_name=dr.source_name,
                        operation="CREATE",
                        time=format_time(file_state.date_created),
                        path=file_state.path,
                    ))

                for file_diff in dr.diff.updated:
                    log.info(TEMPLATE.format(
                        source_name=dr.source_name,
                        operation="UPDATE",
                        time=format_time(file_diff.after.date_updated),
                        path=file_diff.after.path,
                    ))

                for file_state in dr.diff.deleted:
                    log.info(TEMPLATE.format(
                        source_name=dr.source_name,
                        operation="DELETE",
                        time=format_time(dr.diff.run_start),
                        # time=format_time(dr.diff.run_end),
                        path=file_state.path,
                    ))

    except asyncio.CancelledError:
        pass
