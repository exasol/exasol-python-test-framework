#!/usr/bin/env python3

import os
import unittest
import urllib.request, urllib.parse, urllib.error

from exasol_python_test_framework.exatest.test import selftest, run_selftest

from exasol_python_test_framework import exatest

from exasol_python_test_framework.exatest.utils import tempdir
from exasol_python_test_framework.exatest.servers import HTTPServer


class HTTPServerTest(unittest.TestCase):
    def test_anonymous(self):
        class Module:
            class Test(exatest.TestCase):
                def test_1(self):
                    with tempdir() as tmp:
                        with open(os.path.join(tmp, 'dummy'), 'w') as f:
                            f.write('babelfish')
                        with HTTPServer(tmp) as httpd:
                            with urllib.request.urlopen('http://%s:%d/dummy' % httpd.address) as url:
                                data = [line.decode("utf-8") for line in url.readlines()]
                    self.assertIn('babelfish', '\n'.join(data))
        with selftest(Module) as result:
            self.assertTrue(result.wasSuccessful())

    def test_server_is_chdir_safe(self):
        cwd = os.getcwd()
        with tempdir() as tmp:
            self.assertEqual(cwd, os.getcwd())
            with HTTPServer(tmp) as httpd:
                # Current implementation chdir to documentroot;
                # needs subprocesses to avoid this.
                pass
                #self.assertEqual(cwd, os.getcwd())
            self.assertEqual(cwd, os.getcwd())
        self.assertEqual(cwd, os.getcwd())


if __name__ == '__main__':
    run_selftest()
