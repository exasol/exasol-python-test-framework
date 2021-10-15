#!/usr/bin/env python3

import ftplib
import os
import time
import unittest

from exasol_python_test_framework.exatest import useData
from exasol_python_test_framework.exatest.test import selftest, run_selftest

from exasol_python_test_framework import exatest

from exasol_python_test_framework.exatest.utils import tempdir
from exasol_python_test_framework.exatest.servers import FTPServer
from exasol_python_test_framework.exatest.servers.authorizers import DummyAuthorizer


class FTPServerTest(unittest.TestCase):
    def test_anonymous(self):
        class Module:
            class Test(exatest.TestCase):
                def test_1(self):
                    with tempdir() as tmp:
                        with open(os.path.join(tmp, 'dummy'), 'w'):
                            pass
                        with FTPServer(tmp) as ftpd:
                            ftp = ftplib.FTP()
                            ftp.connect(*ftpd.address)
                            ftp.login()
                            data = []
                            ls = ftp.retrlines('LIST', data.append)
                            ftp.quit()
                    self.assertIn('dummy', '\n'.join(data))
        with selftest(Module) as result:
            self.assertTrue(result.wasSuccessful())

    def test_authenticated_user(self):
        class Module:
            class Test(exatest.TestCase):
                def test_1(self):
                    with tempdir() as tmp:
                        with open(os.path.join(tmp, 'dummy'), 'w'):
                            pass
                        auth = DummyAuthorizer()
                        auth.add_user('user', 'passwd', tmp, perm='elradfmw')
                        with FTPServer(tmp, authorizer=auth) as ftpd:
                            ftp = ftplib.FTP()
                            ftp.connect(*ftpd.address)
                            ftp.login('user', 'passwd')
                            ftp.mkd('some_dir')
                            data = []
                            ls = ftp.retrlines('LIST', data.append)
                            ftp.quit()
                    self.assertIn('dummy', '\n'.join(data))
                    self.assertIn('some_dir', '\n'.join(data))
        with selftest(Module) as result:
            self.assertTrue(result.wasSuccessful())

    def test_server_is_chdir_safe(self):
        class Module:
            class Test(exatest.TestCase):
                def test_server_is_chdir_safe(self, x):
                    cwd = os.getcwd()
                    with tempdir() as tmp:
                        self.assertEqual(cwd, os.getcwd())
                        with FTPServer(tmp) as ftpd:
                            time.sleep(0.2) #Without sleep the FTPServer starts and stops immediately which might cause a race condition during shutdown
                            self.assertEqual(cwd, os.getcwd())
                        self.assertEqual(cwd, os.getcwd())
                    self.assertEqual(cwd, os.getcwd())
        with selftest(Module) as result:
            self.assertTrue(result.wasSuccessful())


if __name__ == '__main__':
    run_selftest()
