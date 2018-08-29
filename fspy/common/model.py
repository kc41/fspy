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


# TODO CONSIDER: Save two timestamps (start of scan and end of scan)
# TODO FIX: Use tuples instead of lists
class FullDiff(BaseModel):
    timestamp: datetime

    created: List[FileState]
    deleted: List[FileState]
    updated: List[FileDiff]

    def __bool__(self):
        return bool(self.created) or bool(self.deleted) or bool(self.updated)
