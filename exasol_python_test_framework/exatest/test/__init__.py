"""Exatest test entrypoints."""
# pylint: disable=C0114,C0115,C0116,C0301,C0303,C0305,C0411,C0413,C0103,C0209,C0204,C0415,R1705,R1710,R1720,R1732,R0205,R0903,R0911,R0912,R0913,R0917,R1725,W0105,W0201,W0212,W0221,W0231,W0238,W0511,W0603,W0611,W0612,W0622,W0702,W0718,W0719,W1201,W1202,W1514,I1101

'''Test unittest extensions with unittest'''
import argparse
import io as StringIO
import contextlib
import sys
import unittest
from .. import TestLoader, ClientSetup


def _print_output(output):
    print('\n', '>' * 70, file=sys.stderr)
    print(output, file=sys.stderr)
    print('<' * 70, file=sys.stderr)


def create_setup():
    client_setup = ClientSetup()
    desc = __file__.__doc__
    epilog = ''
    parser = argparse.ArgumentParser(description=desc, epilog=epilog)
    client_setup.odbc_arguments(parser)
    parser.set_defaults(
        logdir='.',
        odbc_log='off',
        driver=None,
    )
    opts = parser.parse_args(sys.argv[1:])
    return opts, client_setup


@contextlib.contextmanager
def selftest(module, debug=False):
    """Context manager to run unittests of unittest extensions in module.

    If debug is False, print test output only if exceptions are raised.

    Usage:

        class SefTest(unittest.TestCase):

            def test_metatest(self):
                class Module:
                    class Test(unittest.TestCase):
                        def test_fail(self):
                            self.fail()

                with selftest(Module) as result:
                    self.assertFalse(result.wasSucessful())
    """

    opts, client_setup = create_setup()
    client_setup.prepare_odbc_init(opts.logdir, opts.server, opts.driver,
                                   opts.user, opts.password, opts.odbc_log)
    try:
        stream = StringIO.StringIO()
        result = unittest.main(module=module,
                               testRunner=unittest.TextTestRunner(stream=stream, verbosity=2),
                               testLoader=TestLoader(dsn=client_setup.dsn, user=opts.user, password=opts.password),
                               argv=sys.argv[:1], exit=False).result
        result.output = stream.getvalue()
        yield result

    except:
        _print_output(stream.getvalue())
        raise
    else:
        if debug:
            _print_output(stream.getvalue())


def run_selftest():
    unittest.main(argv=[sys.argv[0]])
