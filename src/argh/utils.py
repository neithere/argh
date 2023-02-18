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
Utilities
~~~~~~~~~
"""
import argparse
import inspect
import re


def get_subparsers(parser, create=False):
    """
    Returns the `argparse._SubParsersAction` instance for given
    :class:`argparse.ArgumentParser` instance as would have been returned by
    :meth:`argparse.ArgumentParser.add_subparsers`. The problem with the latter
    is that it only works once and raises an exception on the second attempt,
    and the public API seems to lack a method to get *existing* subparsers.

    :param create:
        If `True`, creates the subparser if it does not exist. Default if
        `False`.

    """
    # note that ArgumentParser._subparsers is *not* what is returned by
    # ArgumentParser.add_subparsers().
    if parser._subparsers:
        actions = [
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        ]
        return actions[0]

    if create:
        return parser.add_subparsers()


def get_arg_spec(function):
    """
    Returns argument specification for given function.  Omits special
    arguments of instance methods (`self`) and static methods (usually `cls`
    or something like this).
    """
    while hasattr(function, "__wrapped__"):
        function = function.__wrapped__
    spec = inspect.getfullargspec(function)
    if inspect.ismethod(function):
        spec = spec._replace(args=spec.args[1:])
    return spec


def unindent(text):
    """
    Given a multi-line string, decreases indentation of all lines so that the
    first non-empty line has zero indentation and the remaining lines are
    adjusted accordingly.
    """
    match = re.match("(^|\n)( +)", text)
    if not match:
        return text
    first_line_indentation = match.group(2)
    depth = len(first_line_indentation)
    return re.sub(rf"(^|\n) {{{depth}}}", "\\1", text)
