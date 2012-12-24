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
Assembling
~~~~~~~~~~

Functions and classes to properly assemble your commands in a parser.
"""
import argparse
import inspect

from argh.six import PY3, string_types
from argh.constants import (ATTR_ALIASES, ATTR_ARGS, ATTR_NAME,
                            ATTR_INFER_ARGS_FROM_SIGNATURE)
from argh.utils import Arg, get_subparsers


__all__ = ['SUPPORTS_ALIASES', 'set_default_command', 'add_commands']


def _check_support_aliases():
    p = argparse.ArgumentParser()
    s = p.add_subparsers()
    try:
        s.add_parser('x', aliases=[])
    except TypeError:
        return False
    else:
        return True


SUPPORTS_ALIASES = _check_support_aliases()
""" Calculated on load. If `True`, current version of argparse supports
alternative command names (can be set via :func:`~argh.decorators.aliases`).
"""


def _get_args_from_signature(function):
    if not getattr(function, ATTR_INFER_ARGS_FROM_SIGNATURE, False):
        return

    if PY3:
        spec = inspect.getfullargspec(function)
    else:
        spec = inspect.getargspec(function)

    kwargs = dict(zip(*[reversed(x) for x in (spec.args, spec.defaults or [])]))

    if PY3:
        annotations = dict((k,v) for k,v in function.__annotations__.items()
                           if isinstance(v, str))
    else:
        annotations = {}

    # define the list of conflicting option strings
    # (short forms, i.e. single-character ones)
    chars = [a[0] for a in spec.args]
    char_counts = dict((char, chars.count(char)) for char in set(chars))
    conflicting_opts = tuple(char for char in char_counts
                             if 1 < char_counts[char])

    for name in spec.args:
        flags = []    # name_or_flags
        akwargs = {}  # keyword arguments for add_argument()

        if name in annotations:
            # help message:  func(a : "b")  ->  add_argument("a", help="b")
            akwargs.update(help=annotations.get(name))

        if name in kwargs:
            akwargs.update(default=kwargs.get(name))
            flags = ('-{0}'.format(name[0]), '--{0}'.format(name))
            if name.startswith(conflicting_opts):
                # remove short name
                flags = flags[1:]
        else:
            # positional argument
            flags = (name,)

        # cmd(foo_bar)  ->  add_argument('foo-bar')
        flags = tuple(x.replace('_', '-') for x in flags)

        yield Arg(flags=flags, kwargs=akwargs)


def _guess(arg):
    """
    Adds types, actions, etc. to given argument specification.
    For example, ``default=3`` implies ``type=int``.

    :param arg: a :class:`argh.utils.Arg` instance
    """
    kwargs = arg.kwargs.copy()

    # try guessing some stuff
    if kwargs.get('choices') and not 'type' in kwargs:
        kwargs['type'] = type(kwargs['choices'][0])
    if 'default' in kwargs and not 'action' in kwargs:
        value = kwargs['default']
        if isinstance(value, bool):
            # infer action from default value
            kwargs['action'] = 'store_false' if value else 'store_true'
        elif 'type' not in kwargs and value is not None:
            # infer type from default value
            kwargs['type'] = type(value)

    return Arg(flags=arg.flags, kwargs=kwargs)


def set_default_command(parser, function):
    """ Sets default command (i.e. a function) for given parser.

    If `parser.description` is empty and the function has a docstring,
    it is used as the description.

    .. note::

       An attempt to set default command to a parser which already has
       subparsers (e.g. added with :func:`~argh.assembling.add_commands`)
       results in a `RuntimeError`.

    .. note::

       If there are both explicitly declared arguments (e.g. via
       :func:`~argh.decorators.arg`) and ones inferred from the function
       signature (e.g. via :func:`~argh.decorators.command`), declared ones
       will be merged into inferred ones. If an argument does not conform
       function signature, `ValueError` is raised.

    .. note::

       If the parser was created with ``add_help=True`` (which is by default),
       option name ``-h`` is silently removed from any argument.

    """
    if parser._subparsers:
        raise RuntimeError('Cannot set default command to a parser with '
                           'existing subparsers')

    declared_args = getattr(function, ATTR_ARGS, [])
    inferred_args = list(_get_args_from_signature(function))
    if inferred_args and declared_args:
        # We've got a mixture of declared and inferred arguments

        inferred_dict = dict((x.flags, x.kwargs) for x in inferred_args)
        declared_dict = dict(declared_args)

        for flags, kw in declared_dict.items():
            # 1) make sure that this declared arg conforms to the function
            #    signature and therefore only refines an inferred arg:
            #
            #      @arg('foo')    maps to  func(foo)
            #      @arg('--bar')  maps to  func(bar=...)
            #
            if flags not in inferred_dict:
                raise ValueError('{func}: argument {flags} does not fit '
                                 'function signature: {sig}'.format(
                                    flags=', '.join(flags),
                                    func=function.__name__,
                                    sig=', '.join('/'.join(x) for x in sorted(inferred_dict))))

            # 2) merge declared args into inferred ones (e.g. help=...)
            inferred_dict[flags].update(**kw)

        # pack the modified data back into a list
        inferred_args = [Arg(k,v) for k,v in inferred_dict.items()]

    command_args = inferred_args or declared_args

    # add types, actions, etc. (e.g. default=3 implies type=int)
    command_args = [_guess(x) for x in command_args]

    for a_args, a_kwargs in command_args:
        if parser.add_help and '-h' in a_args:
            a_args = [x for x in a_args if x != '-h']
        try:
            parser.add_argument(*a_args, **a_kwargs)
        except Exception as e:
            raise type(e)('{func}: cannot add arg {args}: {msg}'.format(
                args='/'.join(a_args), func=function.__name__, msg=e))

    if function.__doc__ and not parser.description:
        parser.description = function.__doc__
    parser.set_defaults(function=function)


def add_commands(parser, functions, namespace=None, title=None,
                 description=None, help=None):
    """Adds given functions as commands to given parser.

    :param parser:

        an :class:`argparse.ArgumentParser` instance.

    :param functions:

        a list of functions. A subparser is created for each of them.
        If the function is decorated with :func:`~argh.decorators.arg`, the
        arguments are passed to :class:`argparse.ArgumentParser.add_argument`.
        See also :func:`~argh.dispatching.dispatch` for requirements
        concerning function signatures. The command name is inferred from the
        function name. Note that the underscores in the name are replaced with
        hyphens, i.e. function name "foo_bar" becomes command name "foo-bar".

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

    :param help:

        passed to :meth:`argsparse.ArgumentParser.add_subparsers` as `help`.

    .. note::

        This function modifies the parser object. Generally side effects are
        bad practice but we don't seem to have any choice as ArgumentParser is
        pretty opaque.
        You may prefer :class:`~argh.helpers.ArghParser.add_commands` for a bit
        more predictable API.

    .. admonition:: Design flaw

        This function peeks into the parser object using its internal API.
        Unfortunately the public API does not allow to *get* the subparsers, it
        only lets you *add* them, and do that *once*. So you would have to toss
        the subparsers object around to add something later. That said, I doubt
        that argparse will change a lot in the future as it's already pretty
        stable. If some implementation details would change and break `argh`,
        we'll simply add a workaround a keep it compatibile.

    .. note::

       An attempt to add commands to a parser which already has a default
       function (e.g. added with :func:`~argh.assembling.set_default_command`)
       results in a `RuntimeError`.

    """
    if 'function' in parser._defaults:
        raise RuntimeError('Cannot add commands to a single-command parser')

    subparsers = get_subparsers(parser, create=True)

    if namespace:
        # make a namespace placeholder and register the commands within it
        assert isinstance(namespace, string_types)
        subsubparser = subparsers.add_parser(namespace, help=title)
        subparsers = subsubparser.add_subparsers(title=title,
                                                 description=description,
                                                 help=help)
    else:
        assert not any([title, description, help]), (
            'Arguments "title", "description" or "extra_help" only make sense '
            'if provided along with a namespace.')

    for func in functions:
        # use explicitly defined name; if none, use function name (a_b → a-b)
        cmd_name = getattr(func, ATTR_NAME,
                           func.__name__.replace('_','-'))
        parser_kwargs = {}

        # add command help from function's docstring
        parser_kwargs['help'] = func.__doc__

        # try adding aliases for command name
        if SUPPORTS_ALIASES:
            parser_kwargs['aliases'] = getattr(func, ATTR_ALIASES, [])

        # create and set up the parser for this command
        command_parser = subparsers.add_parser(cmd_name, **parser_kwargs)
        set_default_command(command_parser, func)
