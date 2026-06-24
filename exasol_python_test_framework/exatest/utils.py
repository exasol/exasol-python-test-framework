"""Exatest utility helpers."""
# pylint: disable=C0114,C0115,C0116,C0301,C0303,C0305,C0411,C0103,C0209,C0204,C0415,R1705,R1710,R1720,R1732,R0205,R0903,R0911,R0912,R0913,R0917,R1725,W0201,W0212,W0231,W0238,W0511,W0603,W0611,W0612,W0622,W0702,W0718,W0719,W1201,W1202,W1514,I1101

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
