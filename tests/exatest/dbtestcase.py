#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.realpath(__file__ + '/../../../exasol_python_test_framework'))

import exatest
from exatest.utils import chdir
from exatest import (
        useData,
        )

class TestParameterized(exatest.TestCase):

    @useData((x,) for x in range(10))
    def test_parameterized(self, x):
        self.assertRowsEqual([(None,)], self.query('select * from dual'))

    @useData((x,) for x in range(1000))
    def test_large_parameterized(self, x):
        self.assertRowsEqual([(None,)], self.query('select * from dual'))

class TestSetUp(exatest.TestCase):

    def setUp(self):
        self.query('DROP SCHEMA t1 CASCADE', ignore_errors=True)
        self.query('CREATE SCHEMA t1')

    def test_1(self):
        self.query('select * from dual')

    def test_2(self):
        self.query('select * from dual')

class ODBCTest(exatest.TestCase):
    def test_find_odbcini_after_chdir(self):
        self.assertTrue(os.path.exists('odbc.ini'))
        with chdir('/'):
            self.assertFalse(os.path.exists('odbc.ini'))
            self.query('select * from dual')

if __name__ == '__main__':
    exatest.main()

# vim: ts=4:sts=4:sw=4:et:fdm=indent
