from typing import (
    Dict, Optional, )

import os
from os import path

import logging

from datetime import datetime
import pytz

from fspy.common.model import FileState, FileDiff, FullDiff

log = logging.getLogger(__name__)


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
    def get_diff(old: Dict[str, FileState], new: Dict[str, FileState],
                 run_start: datetime = None, run_end: datetime = None) -> FullDiff:

        now = datetime.now(pytz.utc)

        run_start = now if run_start is None else run_start
        run_end = now if run_end is None else run_end

        return FullDiff(
            run_start=run_start,
            run_end=run_end,

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
        scan_end = datetime.now(pytz.utc)

        if self._ref_snapshot is None:
            self._ref_snapshot = new_snapshot
            return None

        full_diff = self.get_diff(old=self._ref_snapshot, new=new_snapshot,
                                  run_start=scan_start, run_end=scan_end)
        self._ref_snapshot = new_snapshot

        return full_diff
