#!/usr/bin/env python3

import ftplib
import os
import socket
import time
import unittest
from unittest.mock import MagicMock, patch

from exasol_python_test_framework.exatest import useData
from exasol_python_test_framework.exatest.test import selftest, run_selftest

from exasol_python_test_framework import exatest

from exasol_python_test_framework.exatest.utils import tempdir
from exasol_python_test_framework.exatest.servers import FTPServer
from exasol_python_test_framework.exatest.servers.authorizers import DummyAuthorizer
from exasol_python_test_framework.exatest.servers import __main__ as ftp_main


class FTPServerTest(unittest.TestCase):
    def test_cli_forwards_connection_options(self):
        fake_server = MagicMock()
        fake_server.serve_forever.return_value = None
        fake_server.close_all.return_value = None

        argv = [
            "python",
            "-d",
            "/srv",
            "-i",
            "127.0.0.1",
            "-p",
            "2122",
            "-n",
            "198.51.100.10",
            "-r",
            "8000-8002",
        ]
        with patch.object(ftp_main, "FTPServer", return_value=fake_server) as ftp_server:
            with patch("sys.argv", argv):
                ftp_main.main()

        ftp_server.assert_called_once()
        args, kwargs = ftp_server.call_args
        self.assertEqual(("/srv",), args)
        self.assertEqual("127.0.0.1", kwargs["interface"])
        self.assertEqual(2122, kwargs["port"])
        self.assertEqual("198.51.100.10", kwargs["nat_address"])
        self.assertEqual([8000, 8001, 8002], kwargs["passive_ports"])
        self.assertIsInstance(kwargs["authorizer"], DummyAuthorizer)
        fake_server.serve_forever.assert_called_once()
        fake_server.close_all.assert_called_once()

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

    def test_pass_before_user_returns_530(self):
        class Module:
            class Test(exatest.TestCase):
                def test_1(self):
                    with tempdir() as tmp:
                        with FTPServer(tmp) as ftpd:
                            with socket.create_connection(ftpd.address, timeout=5) as conn:
                                reader = conn.makefile("rb")
                                self.assertIn(b"220", reader.readline())
                                conn.sendall(b"PASS secret\r\n")
                                self.assertIn(b"530", reader.readline())
                                conn.sendall(b"QUIT\r\n")
                                self.assertIn(b"221", reader.readline())

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
                def test_server_is_chdir_safe(self):
                    cwd = os.getcwd()
                    with tempdir() as tmp:
                        self.assertEqual(cwd, os.getcwd())
                        with FTPServer(tmp) as ftpd:
                            # Without sleep the FTPServer starts and stops immediately
                            # which might cause a race condition during shutdown
                            time.sleep(0.2)
                            self.assertEqual(cwd, os.getcwd())
                        self.assertEqual(cwd, os.getcwd())
                    self.assertEqual(cwd, os.getcwd())

        with selftest(Module) as result:
            self.assertTrue(result.wasSuccessful())


if __name__ == '__main__':
    run_selftest()
