# -*- coding: utf-8 -*-
#
#  Copyright (c) 2010—2012 Andrey Mikhailenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README for copying conditions.
#
"""
Output Processing
=================
"""
import locale
from argh.six import binary_type, text_type, PY3


__all__ = ['encode_output']


def encode_output(line, output_file, encoding=None):
    """Converts given string to given encoding. If no encoding is specified, it
    is determined from terminal settings or, if none, from system settings.

    .. note:: Compatibility

       :Python 2.x:
           `sys.stdout` is a file-like object that accepts `str` (bytes)
           and breaks when `unicode` is passed to `sys.stdout.write()`.
       :Python 3.x:
           `sys.stdout` is a `_io.TextIOWrapper` instance that accepts `str`
           (unicode) and breaks on `bytes`.

       In Python 2.x arbitrary types are coerced to `unicode` and then to `str`.

       In Python 3.x all types are coerced to `str` with the exception
       for `bytes` which is **not allowed** to avoid confusion.

    """
    if not isinstance(line, text_type):
        if PY3 and isinstance(line, binary_type):
            # in Python 3.x we require Unicode, period.
            raise TypeError('Binary comand output is not supported '
                            'in Python 3.x')

        # in Python 2.x we accept bytes and convert them to Unicode.
        try:
            line = text_type(line)
        except UnicodeDecodeError:
            line = binary_type(line).decode('utf-8')

    if PY3:
        return line

    # Choose output encoding
    if not encoding:
        # choose between terminal's and system's preferred encodings
        if output_file.isatty():
            encoding = getattr(output_file, 'encoding', None)

        encoding = encoding or locale.getpreferredencoding()

    # Convert string from Unicode to the output encoding
    return line.encode(encoding)
