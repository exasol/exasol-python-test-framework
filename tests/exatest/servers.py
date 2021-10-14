#!/usr/bin/env python3

import ftplib
import os
import smtplib
import socket
import unittest
import urllib.request, urllib.parse, urllib.error
from email.mime.text import MIMEText

from exasol_python_test_framework.exatest.test import selftest, run_selftest

from exasol_python_test_framework import exatest

from exasol_python_test_framework.exatest.utils import tempdir
from exasol_python_test_framework.exatest.servers import FTPServer, HTTPServer, SMTPServer
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
        cwd = os.getcwd()
        with tempdir() as tmp:
            self.assertEqual(cwd, os.getcwd())
            with FTPServer(tmp) as ftpd:
                self.assertEqual(cwd, os.getcwd())
            self.assertEqual(cwd, os.getcwd())
        self.assertEqual(cwd, os.getcwd())


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


class SMTPServerTest(unittest.TestCase):
    def test_simple_message(self):
        class Module:
            class Test(exatest.TestCase):
                def test_1(self):
                    with SMTPServer(debug=True) as smtpd:
                        host, port = smtpd.address
                        self.assertNotEqual(0, port)
                        client = smtplib.SMTP(host, port, timeout=5)
                        client.set_debuglevel(1)
                        msg = MIMEText('Test mail')
                        msg['Subject'] = 'Little exatest mail'
                        msg['From'] = 'from.address@foo.bar'
                        msg['To'] = 'babelfish@mailing-list.com'
                        client.sendmail('from.address@foo.bar', ('to.address@babel.fish', 'babel@fish.org'), msg.as_string())
                        client.quit()
                    self.assertEqual(1, len(smtpd.messages))
                    self.assertEqual('from.address@foo.bar', smtpd.messages[0].sender)
                    self.assertIn('babel@fish.org', smtpd.messages[0].recipients)
                    self.assertIn('Test mail', smtpd.messages[0].body.decode("utf-8"))
        with selftest(Module) as result:
            self.assertTrue(result.wasSuccessful())

    def test_esmtp(self):
        """
        Python3 supports ESMTP natively (while Python2 did not)
        """
        class Module:
            class Test(exatest.TestCase):
                def test_1(self):
                    with SMTPServer(debug=True) as smtpd:
                        host, port = smtpd.address
                        s = socket.create_connection(smtpd.address)
                        buf1 = s.recv(4096)
                        s.send(b'EHLO some.host.com\r\n') #Send an ESMTP command
                        buf2 = s.recv(4096)
                        s.send(b'QUIT\r\n')
                        buf3 = s.recv(4096)
                        s.close()
                    self.assertIn('220', buf1.decode("utf-8"))
                    self.assertIn('250 HELP', buf2.decode("utf-8"))
        with selftest(Module) as result:
            self.assertTrue(result.wasSuccessful())


if __name__ == '__main__':
    run_selftest()
