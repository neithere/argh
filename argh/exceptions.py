"""
Exceptions
==========
"""

class CommandError(Exception):
    """The only exception that is wrapped by the dispatcher. Useful for
    print-and-exit tasks.

    Consider the following example::

        def foo(args):
            try:
                ...
            except KeyError as e:
                print(u'Could not fetch item: {0}'.format(e))
                return

    It is exactly the same as::

        def bar(args):
            try:
                ...
            except KeyError as e:
                raise CommandError(u'Could not fetch item: {0}'.format(e))

    This exception can be safely used in both print-style and yield-style
    commands (see :doc:`tutorial`).
    """
