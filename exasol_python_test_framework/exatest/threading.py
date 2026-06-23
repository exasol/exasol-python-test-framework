"""Thread helper with shutdown and exception propagation support."""

import sys
import threading

__all__ = ['Thread', 'ThreadAliveError']


class ThreadAliveError(Exception):
    """Raised when a managed thread is still alive."""


class Thread(threading.Thread):
    """Replacement of threading.Thread for use in TestCase.

    When join'ed, exceptions and assertion are collected.

    Usage:

        class Test(TestCase):
            def thread_fct(self, ...):
                while not self.shutdown_requested():
                    # do something
                self.assertTrue(...)

            def test_with_threads(self):
                t = Thread(target=self.thread_fct, name='thread-name')
                t.start()
                # do something
                t.shutdown() # optional
                t.join(5) # required to collect assertions
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.data = None
        self.__exc_info = None
        self.__shutdown_event = threading.Event()

    def run(self):
        try:
            super().run()
        except Exception:  # pylint: disable=broad-exception-caught
            self.__exc_info = sys.exc_info()

    def join(self, timeout=None):
        super().join(timeout)
        # if self.is_alive():
        #    raise ThreadAliveError("thread '%s' is alive" % self.name)
        if self.__exc_info is not None:
            cls, msg, tb = self.__exc_info
            self.__exc_info = None
            raise cls(f"in thread '{self.name}': {msg}").with_traceback(tb)

    def shutdown(self):
        """Request shutdown for the managed thread."""
        self.__shutdown_event.set()

    def shutdown_requested(self):
        """Return whether shutdown has been requested."""
        return self.__shutdown_event.is_set()

# vim: ts=4:sts=4:sw=4:et:fdm=indent
