#!/usr/bin/env python3

import unittest
import re

from exasol_python_test_framework import exatest

from exasol_python_test_framework.exatest.test import selftest, run_selftest


class ExpectationsTestCaseTest(unittest.TestCase):
    def test_metatest(self):
        class Module:
            class Test(exatest.TestCase):
                def test_pass(self):
                    self.assertExpectations()

                def test_fail(self):
                    self._expectations.append('some traceback')
                    self.assertExpectations()

        with selftest(Module) as result:
            self.assertEqual(1, len(result.failures))
            self.assertEqual(2, result.testsRun)
            self.assertIn('test_pass', result.output)
            self.assertIn('test_fail', result.output)


    def test_getattr(self):
        class Module:
            class Test(exatest.TestCase):
                def assertFoo(self):
                    self.Fail("FOO")

                def test_x(self):
                    self.expectFoo()

        with selftest(Module) as result:
            self.assertIn('FOO', result.output)
            self.assertIn('FAILED', result.output)

    def test_getattr_unknown_assert(self):
        class Module:
            class Test(exatest.TestCase):
                def test_x(self):
                    self.expectFoo()

        with selftest(Module) as result:
            self.assertIn("AttributeError: 'Test' object has no attribute 'expectFoo'", result.output)

    def test_expectations_are_non_fatal(self):
        class Module:
            class Test(exatest.TestCase):
                def test_x(self):
                    self.expectTrue(False)
                    self.assertEqual(1, 2)

        with selftest(Module) as result:
            self.assertIn('False is not true', result.output)
            self.assertIn('1 != 2', result.output)

    def test_assertExpectations(self):
        class Module:
            class Test(exatest.TestCase):
                def test_x(self):
                    self.expectTrue(False)
                    self.assertExpectations()

        with selftest(Module) as result:
            self.assertIn("ExpectationError", result.output)
            self.assertIn("FAILED", result.output)

    def test_missing_assertExpectations_results_in_error(self):
        class Module:
            class Test(exatest.TestCase):
                def test_x(self):
                    self.expectTrue(False)

        with selftest(Module) as result:
            self.assertIn("ExpectationError", result.output)
            self.assertIn("FAILED", result.output)

    def test_assertExpectations_contextmanager(self):
        class Module:
            class Test(exatest.TestCase):
                def test_x(self):
                    with self.expectations():
                        self.expectTrue(False)
                    self.assertEqual(1,2)

        with selftest(Module) as result:
            self.assertIn("ExpectationError", result.output)
            self.assertNotIn('1 != 2', result.output)
            self.assertNotIn("ERROR", result.output)

    def test_traceback_is_in_right_order(self):
        class Module:
            class Test(exatest.TestCase):
                def first(self):
                    self.expectTrue(False)
                def second(self):
                    self.first()
                def third(self):
                    self.second()
                def test_x(self):
                    self.third()

        with selftest(Module) as result:
            self.assertTrue(re.search('third.*second.*first', result.output, re.DOTALL))


if __name__ == '__main__':
    run_selftest()
