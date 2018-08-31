# TODO CONSIDER: Use named tuples for internal operations and convert to pydantic.BaseModel only during sending
from datetime import datetime
from typing import List

from pydantic import BaseModel


class FileState(BaseModel):
    path: str
    date_created: datetime
    date_updated: datetime
    size: int


class FileDiff(BaseModel):
    before: FileState = None
    after: FileState = None


# TODO FIX: Use tuples instead of lists
class FullDiff(BaseModel):
    run_start: datetime
    run_end: datetime

    created: List[FileState]
    deleted: List[FileState]
    updated: List[FileDiff]

    def __bool__(self):
        return bool(self.created) or bool(self.deleted) or bool(self.updated)


class DiffReport(BaseModel):
    source_name: str
    diff: FullDiff


class DiffReportHandlingResponse(BaseModel):
    handled: bool
    message: str = None
