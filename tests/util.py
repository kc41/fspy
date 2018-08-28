from typing import Dict, Union

import tempfile
from functools import wraps
from os import path, makedirs


def create_file_struct(base_dir: str, struct: Dict[str, Union[int, dict]]):
    for k, v in struct.items():
        if isinstance(v, int):
            file_name = path.join(base_dir, k)

            with open(file_name, "wb") as out_file:
                out_file.seek(v - 1)
                out_file.write(b"\0")

        elif isinstance(v, dict):
            next_dir_path = path.join(base_dir, k)
            makedirs(next_dir_path)

            create_file_struct(next_dir_path, v)


def with_file_structure(struct: Dict[str, Union[int, dict]]):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                create_file_struct(tmp_dir_name, struct)

                func(*args, wd=tmp_dir_name, **kwargs)

        return wrapped

    return wrapper
