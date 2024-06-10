#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path


from exasol_python_test_framework.exatest.utils import obj_from_json_file
from exasol_python_test_framework.exatest.test import run_selftest


class UtilsTest(unittest.TestCase):
    def test_info_object(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            sample_dict = {"a": {"b": {"c": 100}}}
            tmp_file = Path(tmpdirname) / "tmp.json"
            with open (tmp_file, "w") as f:
                json.dump(sample_dict, f)
            o = obj_from_json_file(tmp_file)
            self.assertEqual(o.a.b.c, 100)


if __name__ == '__main__':
    run_selftest()
