# -*- coding: utf-8 -*-
"""
API reference
=============

"""
__all__ = ['ArghParser', 'arg', 'plain_signature', 'add_commands', 'dispatch']
__version__ = '0.1.0'

import sys
from functools import wraps
import argparse


def plain_signature(func):
    """Marks that given function expects ordinary positional and named
    arguments instead of a single positional argument (a
    :class:`argparse.Namespace` object). Useful for existing functions that you
    don't want to alter nor write wrappers by hand.
    """
    func.argh_no_namespace = True
    return func

def arg(*args, **kwargs):
    """Declares an argument for given function. Does not register the function
    anywhere, not does it modify the function in any way.
    """
    kwargs = kwargs.copy()
    if 'type' not in kwargs and kwargs.get('default') is not None:
        kwargs['type'] = type(kwargs['default'])
    def wrapper(func):
        func.argh_args = getattr(func, 'argh_args', [])
        func.argh_args.append((args, kwargs))
        return func
    return wrapper

def _get_subparsers(parser):
    """Returns the :class:`argparse._SupParsersAction` instance for given
    :class:`ArgumentParser` instance as would have been returned by
    :meth:`ArgumentParser.add_subparsers`. The problem with the latter is that
    it only works once and raises an exception on the second attempt, and the
    public API seems to lack a method to get *existing* subparsers.
    """
    # note that ArgumentParser._subparsers is *not* what is returned by
    # ArgumentParser.add_subparsers().
    if parser._subparsers:
        actions = [a for a in parser._actions
                   if isinstance(a, argparse._SubParsersAction)]
        assert len(actions) == 1
        return actions[0]
    else:
        return parser.add_subparsers()

def add_commands(parser, functions, namespace=None, title=None,
                 description=None, extra_help=None):
    """Adds given functions as commands to given parser.

    :param parser:
        an :class:`argparse.ArgumentParser` instance.
    :param functions:
        A list of functions. If the function is decorated with :func:`arg`
        The underscores are replaced with hyphens, i.e. function name "foo_bar"
        becomes command name "foo-bar".
    :param namespace:
        an optional string representing the group of commands. For example, if
        a command named "hello" is added without the namespace, it will be
        available as "prog.py hello"; if the namespace if specified as "greet",
        then the command will be accessible as "prog.py greet hello". The
        namespace itself is not callable, so "prog.py greet" will fail and only
        display a help message.

    Help message for a namespace can be also tuned with these params (provided
    that you specify the `namespace`):

    :param title:
        passed to :meth:`argsparse.ArgumentParser.add_subparsers` as `title`.
    :param description:
        passed to :meth:`argsparse.ArgumentParser.add_subparsers` as
        `description`.
    :param extra_help:
        passed to :meth:`argsparse.ArgumentParser.add_subparsers` as `help`.

    .. note::

        This function modifies the parser object. Generally side effects are
        bad practice but we don't seem to have any choice as ArgumentParser is
        pretty opaque. You may prefer :class:`ArghParser.add_commands` for a
        bit more predictable API.

    .. admonition:: Design flaw

        This function peeks into the parser object using its internal API.
        Unfortunately the public API does not allow to *get* the subparsers, it
        only lets you *add* them, and do that *once*. So you'd have to toss the
        subparsers object around to add something later.

    """
    subparsers = _get_subparsers(parser)

    if namespace:
        # make a namespace placeholder and register the commands within it
        assert isinstance(namespace, str)
        subsubparser = subparsers.add_parser(namespace)
        subparsers = subsubparser.add_subparsers(title=title,
                                                description=description,
                                                help=extra_help)
    else:
        assert not any([title, description, extra_help]), (
            'Arguments "title", "description" or "extra_help" only make sense '
            'if provided along with a namespace.')

    for func in functions:
        name = func.__name__.replace('_','-')
        help = func.__doc__
        command_parser = subparsers.add_parser(name, help=help)
        for a_args, a_kwargs in getattr(func, 'argh_args', []):
            command_parser.add_argument(*a_args, **a_kwargs)
        command_parser.set_defaults(function=func, help=func.__doc__)

def dispatch(parser, argv=None, print_result=True, add_help_command=True):
    """Parses given list of arguments using given parser, calls the relevant
    function passing the :class:`argparse.Namespace` object to it and prints
    the result.

    The target function should expect one positional argument: the
    :class:`argparse.Namespace` object. However, if the function is decorated with
    :func:`plain_signature`, the positional and named arguments from the
    namespace object are passed to the function instead of the object itself.

    :param parser:
        the ArgumentParser instance.
    :param argv:
        a list of strings representing the arguments. If `None`, ``sys.argv``
        is used instead. Default is `None`.
    :param print_result:
        if `True`, the result is printed and returned to the caller. If
        `False`, it is only returned and not printed. Default is `True`.
    :param add_help_command:
        if `True`, converts first positional argument "help" to a keyword
        argument so that ``help foo`` becomes ``foo --help`` and displays usage
        information for "foo". Default is `True`.

    """
    if argv is None:
        argv = sys.argv[1:]
    if add_help_command:
        if argv and argv[0] == 'help':
            argv.pop(0)
            argv.append('--help')
    # this will raise SystemExit if parsing fails
    args = parser.parse_args(argv)
    if getattr(args.function, 'argh_no_namespace', False):
        # filter the namespace variables so that only those expected by the
        # actual function will pass
        f = args.function
        expected_args = f.func_code.co_varnames[:f.func_code.co_argcount]
        ok_args = [x for x in args._get_args() if x in expected_args]
        ok_kwargs = dict((k,v) for k,v in args._get_kwargs()
                         if k in expected_args)
        result = args.function(*ok_args, **ok_kwargs)
    else:
        result = args.function(args)
    if print_result:
        print(result)
    return result


class ArghParser(argparse.ArgumentParser):
    """An :class:`ArgumentParser` suclass which adds a couple of convenience
    methods.

    There is actually no need to subclass the parser. The methods are but
    wrappers for stand-alone functions :func:`add_commands` and
    :func:`dispatch`.
    """
    def add_commands(self, *args, **kwargs):
        "Wrapper for :func:`add_commands`."
        return add_commands(self, *args, **kwargs)

    def dispatch(self, *args, **kwargs):
        "Wrapper for :func:`dispatch`."
        return dispatch(self, *args, **kwargs)
