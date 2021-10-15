#!/usr/bin/env python3

import smtplib
import socket
import unittest
from email.mime.text import MIMEText

from exasol_python_test_framework.exatest.test import selftest, run_selftest

from exasol_python_test_framework import exatest

from exasol_python_test_framework.exatest.servers import SMTPServer


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
                    self.assertIn('250', buf2.decode("utf-8"))
        with selftest(Module) as result:
            self.assertTrue(result.wasSuccessful())


if __name__ == '__main__':
    run_selftest()
