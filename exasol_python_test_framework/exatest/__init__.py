import types

import argparse
import contextlib
import cProfile
import inspect
import logging
import os
import pdb
import pstats
import sys
import tempfile
import time
import unittest
import socket

from unittest import (
        SkipTest,
        suite,
        case,
        util
        )

import pyodbc

from .clients.client_setup import ClientSetup
from .threading import Thread
from .testcase import *

@contextlib.contextmanager
def os_timer():
    before = os.times()
    try:
        yield
    finally:
        after = os.times()
        print('\nreal %7.2fs\nuser %7.2fs\nsys  %7.2fs\n' % (
            after[4] - before[4], after[0] - before[0], after[1] - before[1]))

@contextlib.contextmanager
def timer():
    class Timer(object):
        def __init__(self):
            self.start = time.time()
            self.stop = None
            self.duration = None
    t = Timer()
    try:
        yield t
    finally:
        t.stop = time.time()
        t.duration = t.stop - t.start

class TestLoader(unittest.TestLoader):
    '''Load tests like the default TestLoader, but sorted by line numbers'''

    def __init__(self, **kwargs):
        self.kwargs=kwargs

    def getTestCaseNames(self, testCaseClass):
        '''Return a sorted sequence of method names found within testCaseClass'''
        def isTestMethod(attrname, testCaseClass=testCaseClass,
                prefix=self.testMethodPrefix):
            return (attrname.startswith(prefix) and
                    hasattr(getattr(testCaseClass, attrname), '__call__'))
        testFnNames = list(filter(isTestMethod, dir(testCaseClass)))
        return sorted(testFnNames, key=lambda x: get_sort_key(getattr(testCaseClass, x)))

    def loadTestsFromModule(self, module, use_load_tests=True):
        '''Return a suite of all tests cases contained in the given module'''
        tests = []
        objects = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, TestCase):
                # Sort by line number and break ties with the class name.
                objects.append((inspect.getsourcelines(obj)[1], obj.__name__, obj))
        # This breaks if you define two classes with the same name on the same line numbers and try to run both at
        # the same time. Please don't do this :)
        for _, _, obj in sorted(objects):
            tests.append(self.loadTestsFromTestCase(obj))
        load_tests = getattr(module, 'load_tests', None)
        tests = self.suiteClass(tests)
        if use_load_tests and load_tests is not None:
            try:
                return load_tests(self, tests, None)
            except Exception as e:
                return unittest._make_failed_load_tests(module.__name__, e,
                                               self.suiteClass)
        return tests

    def loadTestsFromTestCase(self, testCaseClass):
        """Return a suite of all tests cases contained in 
           testCaseClass."""
        if issubclass(testCaseClass, suite.TestSuite):
            raise TypeError("Test cases should not be derived from "
                            "TestSuite. Maybe you meant to derive from"
                            " TestCase?")
        testCaseNames = self.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
            testCaseNames = ['runTest']

        # Modification here: parse keyword arguments to testCaseClass.
        test_cases = []
        for test_case_name in testCaseNames:
            test_cases.append(testCaseClass(test_case_name, **self.kwargs))
        loaded_suite = self.suiteClass(test_cases)

        return loaded_suite 

    def loadTestsFromName(self, name, module=None):
        """Return a suite of all test cases given a string specifier.
        The name may resolve either to a module, a test case class, a
        test method within a test case class, or a callable object which
        returns a TestCase or TestSuite instance.
        The method optionally resolves the names relative to a given module.
        """
        parts = name.split('.')
        error_case, error_message = None, None
        if module is None:
            parts_copy = parts[:]
            while parts_copy:
                try:
                    module_name = '.'.join(parts_copy)
                    module = __import__(module_name)
                    break
                except ImportError:
                    next_attribute = parts_copy.pop()
                    # Last error so we can give it to the user if needed.
                    error_case, error_message = _make_failed_import_test(
                        next_attribute, self.suiteClass)
                    if not parts_copy:
                        # Even the top level import failed: report that error.
                        self.errors.append(error_message)
                        return error_case
            parts = parts[1:]
        obj = module
        for part in parts:
            try:
                parent, obj = obj, getattr(obj, part)
            except AttributeError as e:
                # We can't traverse some part of the name.
                if (getattr(obj, '__path__', None) is not None
                    and error_case is not None):
                    # This is a package (no __path__ per importlib docs), and we
                    # encountered an error importing something. We cannot tell
                    # the difference between package.WrongNameTestClass and
                    # package.wrong_module_name so we just report the
                    # ImportError - it is more informative.
                    self.errors.append(error_message)
                    return error_case
                else:
                    # Otherwise, we signal that an AttributeError has occurred.
                    error_case, error_message = _make_failed_test(
                        part, e, self.suiteClass,
                        'Failed to access attribute:\n%s' % (
                            traceback.format_exc(),))
                    self.errors.append(error_message)
                    return error_case

        if isinstance(obj, types.ModuleType):
            return self.loadTestsFromModule(obj)
        elif isinstance(obj, type) and issubclass(obj, case.TestCase):
            return self.loadTestsFromTestCase(obj)
        elif (isinstance(obj, types.FunctionType) and
              isinstance(parent, type) and
              issubclass(parent, case.TestCase)):
            name = parts[-1]
            inst = parent(name,**self.kwargs)
            # static methods follow a different path
            if not isinstance(getattr(inst, name), types.FunctionType):
                return self.suiteClass([inst])
        elif isinstance(obj, suite.TestSuite):
            return obj
        if callable(obj):
            test = obj(**self.kwargs)
            if isinstance(test, suite.TestSuite):
                return test
            elif isinstance(test, case.TestCase):
                return self.suiteClass([test])
            else:
                raise TypeError("calling %s returned %s, not a test" %
                                (obj, test))
        else:
            raise TypeError("don't know how to make test from: %s" % obj)


class TestProgram(object):
    logger_name = 'exatest.main'

    def __init__(self):
        self._client_setup = ClientSetup()
        self.opts = self._parse_opts()
        self.init_logger()
        self.opts.log = logging.getLogger(self.logger_name)
        self._run()

    def init_logger(self):
        '''initialize logging'''
        datefmt = '%Y-%m-%d %H:%M:%S'
        format = '%(asctime)s.%(msecs)03d '
        #format += os.uname()[1] + ' '
        format += '%(levelname)s '
        format += '[%(name)s] '
        format += '%(message)s'
        formatter = logging.Formatter(format, datefmt)
        logfile = os.path.splitext(os.path.basename(sys.argv[0]))[0] + '.log'
        handler = logging.FileHandler(os.path.join(self.opts.logdir, logfile), mode='w')
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        console = logging.StreamHandler()
        console.setLevel(self.opts.loglevel)
        console.setFormatter(formatter)

        root = logging.getLogger('')
        root.addHandler(handler)
        root.addHandler(console)
        root.setLevel(logging.DEBUG)

    def _parse_opts(self):
        desc = self.__doc__
        epilog = ''
        parser = argparse.ArgumentParser(description=desc, epilog=epilog)
        parser.add_argument('-v', '--verbose', action='store_const', const=2,
            dest='verbosity', help='verbose output')
        parser.add_argument('-q', '--quiet', action='store_const', const=0,
            dest='verbosity', help='minimal output')
        parser.add_argument('-f', '--failfast', action='store_true',
            help='stop on first failure')

        parser.add_argument('tests', nargs='*',
            help='classes or methods to run in the form "TestCaseClass" or "TestCaseClass.test_method" (default: run all tests)')

        self._client_setup.odbc_arguments(parser.add_argument_group('ODBC specific'))

        debug = parser.add_argument_group('generic options')
        choices = ('critical', 'error', 'warning', 'info', 'debug')
        debug.add_argument('--loglevel', choices=choices,
            help='set loglevel for console output (default: %(default)s)')
        debug.add_argument('--debugger', action='store_true',
            help='run program under pdb (Python debugger)')
        debug.add_argument('--profiler', action='store_true',
            help='run program with profiler')
        parser.set_defaults(
                verbosity=1,
                failfast=False,
                logdir='.',
                loglevel='warning',
                odbc_log='off',
                tls_cert='unverified',
                connect=None,
                driver=None,
                debugger=False,
                profiler=False,
                )
        self.parser_hook(parser)
        opts = parser.parse_args()
        opts.loglevel = getattr(logging, opts.loglevel.upper())
        opts.unittest_args = sys.argv[0:1] + opts.tests
        return opts

    def parser_hook(self, parser):
        '''extend parser in sub classes'''
        pass

    def _run(self):
        with os_timer():
            if self.opts.profiler:
                with tempfile.NamedTemporaryFile() as tmp:
                    cProfile.runctx('self._main()', globals(), locals(), tmp.name)
                    s = pstats.Stats(tmp.name)
                    s.sort_stats("cumulative").print_stats(50)
            elif self.opts.debugger:
                pdb.runcall(self._main)
            else:
                self._main()

    def prepare_hook(self):
        '''extend preperation in sub classes
        
        Return True if successful.'''
        return True

    def _main(self):
        self.opts.log.info('prepare for tests')
        self._client_setup.prepare_odbc_init(
            self.opts.logdir,
            self.opts.server,
            self.opts.driver,
            self.opts.user,
            self.opts.password,
            self.opts.odbc_log,
            self.opts.tls_cert,
        )
        prepare_ok = self.prepare_hook()
        self.opts.log.info('starting tests')
        testprogram = unittest.main(
                argv=self.opts.unittest_args,
                failfast=self.opts.failfast,
                verbosity=self.opts.verbosity,
                testLoader=TestLoader(dsn=self._client_setup.dsn, user=self.opts.user, password=self.opts.password),
                exit=False,
                )
        self.opts.log.info('finished tests')
        rc = 0 if (prepare_ok and
                testprogram.result.wasSuccessful() and
                len(testprogram.result.unexpectedSuccesses) == 0) else 1
        sys.exit(rc)

    def _resolve_host_to_ipv4(self,server):
        host_port_split=server.split(":")
        host_port_split[0] = socket.gethostbyname(host_port_split[0])
        return ":".join(host_port_split)


main = TestProgram

# vim: ts=4:sts=4:sw=4:et:fdm=indent
