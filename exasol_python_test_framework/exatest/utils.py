import json
from contextlib import contextmanager
import os
import shutil
import tempfile
from typing import Union


@contextmanager
def tempdir():
    tmp = tempfile.mkdtemp()
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp)

@contextmanager
def chdir(newdir):
    olddir = os.getcwd()
    try:
        os.chdir(newdir)
        yield
    finally:
        os.chdir(olddir)


class InfoObject:
    """
    Recursive class which converts a given dictionary to attributes of the instance.
    This is just a convenience class.
    """
    def __init__(self, d):
        for k, v in d.items():
            if isinstance(k, (list, tuple)):
                setattr(self, k, [InfoObject(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(self, k, InfoObject(v) if isinstance(v, dict) else v)


def obj_from_json_file(json_file_path: Union[str, bytes, os.PathLike]) -> InfoObject:
    with open(json_file_path, "r") as f:
        env_info_dict = json.load(f)
        return InfoObject(env_info_dict)

# vim: ts=4:sts=4:sw=4:et:fdm=indent

