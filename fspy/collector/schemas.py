from typing import Optional, List

from datetime import datetime
from pydantic import BaseModel

from fspy.collector import db


class FlatReportEntrySchema(BaseModel):
    source_name: str
    source_ip: Optional[str]

    file_path: str
    operation: db.OperationsEnum

    size_before: Optional[int]
    size_after: Optional[int]

    operation_time: datetime


class FlatReportSchema(BaseModel):
    entries: List[FlatReportEntrySchema]
