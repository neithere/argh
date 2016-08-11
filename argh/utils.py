# coding: utf-8
#
#  Copyright © 2010—2014 Andrey Mikhaylenko and contributors
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

from argh import compat
from argh.parse_sphinx import parse_sphinx_doc


def get_subparsers(parser, create=False):
    """
    Returns the :class:`argparse._SubParsersAction` instance for given
    :class:`ArgumentParser` instance as would have been returned by
    :meth:`ArgumentParser.add_subparsers`. The problem with the latter is that
    it only works once and raises an exception on the second attempt, and the
    public API seems to lack a method to get *existing* subparsers.

    :param create:
        If `True`, creates the subparser if it does not exist. Default if
        `False`.

    """
    # note that ArgumentParser._subparsers is *not* what is returned by
    # ArgumentParser.add_subparsers().
    if parser._subparsers:
        actions = [a for a in parser._actions
                   if isinstance(a, argparse._SubParsersAction)]
        assert len(actions) == 1
        return actions[0]
    else:
        if create:
            return parser.add_subparsers()


def get_arg_spec(function):
    """
    Returns argument specification for given function.  Omits special
    arguments of instance methods (`self`) and static methods (usually `cls`
    or something like this).
    """
    spec = compat.getargspec(function)
    if inspect.ismethod(function):
        spec = spec._replace(args=spec.args[1:])
    return spec


def func_kwargs_args(function):
    """
    Return a dict which specifies which arguments of a function are key-word (True) or positional (False)
    :param func: A method or function
    :return: A dict - keys args/kwargs names : True if keyword arg, False if not
    """
    args, varargs, varkw, argspec_defaults = get_arg_spec(function)

    defaults = {}
    if argspec_defaults is not None:
        defaults = dict(zip(reversed(args), reversed(argspec_defaults)))

    args_dict = {}
    for arg in args:
        args_dict[arg] = arg in defaults    # If in True, else False

    return args_dict


def parse_description(func, format='sphinx'):
    """
    Returns the function description from the docstring

    :param func: A function
    :param format: Which docstring format
    :return: String of the description
    """

    if format not in ['sphinx']:
        raise NotImplementedError("sphinx is currently only supported")

    return parse_sphinx_doc(func.__doc__).get('description', None)