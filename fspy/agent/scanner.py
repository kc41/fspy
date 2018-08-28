from typing import (
    Dict, Optional, List,
    NamedTuple,
)

import os
from os import path

import logging

from datetime import datetime
import pytz

log = logging.getLogger(__name__)


class FileState(NamedTuple):
    path: str
    date_created: datetime
    date_updated: datetime
    size: int


class FileDiff(NamedTuple):
    before: FileState = None
    after: FileState = None


# TODO CONSIDER: Save two timestamps (start of scan and end of scan)
# TODO FIX: Use tuples instead of lists
class FullDiff(NamedTuple):
    timestamp: datetime

    created: List[FileState]
    deleted: List[FileState]
    updated: List[FileDiff]

    def __bool__(self):
        return bool(self.created) or bool(self.deleted) or bool(self.updated)


def _file_state_from_file_path(file_path: str) -> FileState:
    stat_info = os.stat(file_path)

    return FileState(
        path=file_path,
        date_created=datetime.fromtimestamp(stat_info.st_ctime, pytz.utc),
        date_updated=datetime.fromtimestamp(stat_info.st_mtime, pytz.utc),
        size=stat_info.st_size
    )


class SimpleComparator:
    def __init__(self, dir_path: str):
        if not os.path.isabs(dir_path):
            dir_path = path.abspath(dir_path)

        base_error_text = f"Can not create SimpleComparator for '{dir_path}'"

        if not path.exists(dir_path):
            raise ValueError(f"{base_error_text}: not exists")

        if not path.isdir(dir_path):
            raise ValueError(f"{base_error_text}: not a directory")

        self._dir_path = dir_path
        self._ref_snapshot = None  # type: Dict[str, FileState]

    def get_snapshot(self) -> Dict[str, FileState]:
        new_snapshot = {}

        for dir_path, dirs, files in os.walk(self._dir_path):
            for fn in files:
                full_fn = path.join(dir_path, fn)

                new_snapshot[full_fn] = _file_state_from_file_path(full_fn)

        return new_snapshot

    @staticmethod
    def get_diff(old: Dict[str, FileState], new: Dict[str, FileState], timestamp=None) -> FullDiff:
        if timestamp is None:
            timestamp = datetime.now(pytz.utc)

        return FullDiff(
            timestamp=timestamp,

            created=[new[fn] for fn in new.keys() - old.keys()],
            deleted=[old[fn] for fn in old.keys() - new.keys()],
            updated=[
                FileDiff(
                    before=old[fn],
                    after=new[fn],
                )
                for fn in old.keys() & new.keys()
                if old[fn] != new[fn]
            ],
        )

    def scan(self) -> Optional[FullDiff]:
        scan_start = datetime.now(pytz.utc)
        new_snapshot = self.get_snapshot()

        if self._ref_snapshot is None:
            self._ref_snapshot = new_snapshot
            return None

        full_diff = self.get_diff(old=self._ref_snapshot, new=new_snapshot, timestamp=scan_start)
        self._ref_snapshot = new_snapshot

        return full_diff
