# based on "six" by Benjamin Peterson

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

