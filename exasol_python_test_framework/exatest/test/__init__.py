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

