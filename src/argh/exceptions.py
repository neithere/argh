#
#  Copyright © 2010—2023 Andrey Mikhaylenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README.rst for copying conditions.
#
"""
Exceptions
~~~~~~~~~~
"""


class AssemblingError(Exception):
    """
    Raised if the parser could not be configured due to malformed
    or conflicting command declarations.
    """


class DispatchingError(Exception):
    """
    Raised if the dispatching could not be completed due to misconfiguration
    which could not be determined on an earlier stage.
    """


class CommandError(Exception):
    """
    Intended to be raised from within a command.  The dispatcher wraps this
    exception by default and prints its message without traceback, then exits
    with exit code 1.

    Useful for print-and-exit tasks when you expect a failure and don't want
    to startle the ordinary user by the cryptic output.

    Consider the following example::

        def foo(args):
            try:
                ...
            except KeyError as e:
                print(u"Could not fetch item: {0}".format(e))
                sys.exit(1)

    It is exactly the same as::

        def bar(args):
            try:
                ...
            except KeyError as e:
                raise CommandError(u"Could not fetch item: {0}".format(e))

    To customize the exit status, pass an integer (as per ``sys.exit()``) to
    the ``code`` keyword arg.

    This exception can be safely used in both print-style and yield-style
    commands (see :doc:`tutorial`).
    """

    def __init__(self, *args, code=None):
        self.code = code
        super(CommandError, self).__init__(*args)
