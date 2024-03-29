#!/usr/bin/env python

"""
Compatibility module similar to six which helps maintaining
a single code base working with python from 2.6 to 3.x.
"""

import os
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    def u(s):
        return s

    def b(s):
        return s.encode("latin-1")

    getcwdu = os.getcwd
    str = str
    xrange = range
else:
    def u(s):
        return str(s)

    def b(s):
        return s

    getcwdu = os.getcwd
    str = str
    xrange = xrange


# removed in 3.0, reintroduced in 3.2
try:
    callable = callable
except Exception:
    def callable(obj):
        for klass in type(obj).__mro__:
            if "__call__" in klass.__dict__:
                return True
        return False
