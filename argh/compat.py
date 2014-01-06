# originally inspired by "six" by Benjamin Peterson

import inspect
import sys


if sys.version_info < (3,0):
    text_type = unicode
    binary_type = str

    import StringIO
    StringIO = BytesIO = StringIO.StringIO
else:
    text_type = str
    binary_type = bytes

    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO


if sys.version_info < (3,0):
    getargspec = inspect.getargspec
else:
    # in Python 3 the basic getargspec doesn't support keyword-only arguments
    # and annotations and raises ValueError if they are discovered
    getargspec = inspect.getfullargspec


class _PrimitiveOrderedDict(dict):
    """
    A poor man's OrderedDict replacement for compatibility with Python 2.6.
    Implements only the basic features.  May easily break if non-overloaded
    methods are used.
    """
    def __init__(self, *args, **kwargs):
        super(_PrimitiveOrderedDict, self).__init__(*args, **kwargs)
        self._seq = []

    def __setitem__(self, key, value):
        super(_PrimitiveOrderedDict, self).__setitem__(key, value)
        if key not in self._seq:
            self._seq.append(key)

    def __delitem__(self, key):
        super(_PrimitiveOrderedDict, self).__delitem__(key)
        idx = self._seq.index(key)
        del self._seq[idx]

    def __iter__(self):
        return iter(self._seq)

    def keys(self):
        return list(self)

    def values(self):
        return [self[k] for k in self]


try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = _PrimitiveOrderedDict
