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
Assembling
~~~~~~~~~~

Functions and classes to properly assemble your commands in a parser.
"""
import argparse
import sys

from argh.completion import COMPLETION_ENABLED
from argh.compat import OrderedDict
from argh.constants import (ATTR_ALIASES, ATTR_ARGS, ATTR_NAME,
                            ATTR_INFER_ARGS_FROM_SIGNATURE,
                            ATTR_EXPECTS_NAMESPACE_OBJECT,
                            PARSER_FORMATTER, DEFAULT_ARGUMENT_TEMPLATE)
from argh.utils import get_subparsers, get_arg_spec
from argh.exceptions import AssemblingError


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
"""
Calculated on load. If `True`, current version of argparse supports
alternative command names (can be set via :func:`~argh.decorators.aliases`).
"""


def _get_args_from_signature(function):
    if getattr(function, ATTR_EXPECTS_NAMESPACE_OBJECT, False):
        return

    spec = get_arg_spec(function)

    defaults = dict(zip(*[reversed(x) for x in (spec.args,
                                                spec.defaults or [])]))
    defaults.update(getattr(spec, 'kwonlydefaults', None) or {})

    kwonly = getattr(spec, 'kwonlyargs', [])

    if sys.version_info < (3,0):
        annotations = {}
    else:
        annotations = dict((k,v) for k,v in function.__annotations__.items()
                           if isinstance(v, str))

    # define the list of conflicting option strings
    # (short forms, i.e. single-character ones)
    chars = [a[0] for a in spec.args + kwonly]
    char_counts = dict((char, chars.count(char)) for char in set(chars))
    conflicting_opts = tuple(char for char in char_counts
                             if 1 < char_counts[char])

    for name in spec.args + kwonly:
        flags = []    # name_or_flags
        akwargs = {}  # keyword arguments for add_argument()

        if name in annotations:
            # help message:  func(a : "b")  ->  add_argument("a", help="b")
            akwargs.update(help=annotations.get(name))

        if name in defaults or name in kwonly:
            if name in defaults:
                akwargs.update(default=defaults.get(name))
            else:
                akwargs.update(required=True)
            flags = ('-{0}'.format(name[0]), '--{0}'.format(name))
            if name.startswith(conflicting_opts):
                # remove short name
                flags = flags[1:]

        else:
            # positional argument
            flags = (name,)

        # cmd(foo_bar)  ->  add_argument('foo-bar')
        flags = tuple(x.replace('_', '-') for x in flags)

        yield dict(option_strings=flags, **akwargs)

    if spec.varargs:
        # *args
        yield dict(option_strings=[spec.varargs], nargs='*')


def _guess(kwargs):
    """
    Adds types, actions, etc. to given argument specification.
    For example, ``default=3`` implies ``type=int``.

    :param arg: a :class:`argh.utils.Arg` instance
    """
    guessed = {}

    TYPE_AWARE_ACTIONS = 'store', 'append'
    "Parser actions that accept argument 'type'."

    # guess type/action from default value
    value = kwargs.get('default')
    if value is not None:
        if isinstance(value, bool):
            if kwargs.get('action') is None:
                # infer action from default value
                guessed['action'] = 'store_false' if value else 'store_true'
        elif kwargs.get('type') is None:
            # infer type from default value
            # (make sure that action handler supports this keyword)
            if kwargs.get('action', 'store') in TYPE_AWARE_ACTIONS:
                guessed['type'] = type(value)

    # guess type from choices (first item)
    if kwargs.get('choices') and 'type' not in list(guessed) + list(kwargs):
        guessed['type'] = type(kwargs['choices'][0])

    return dict(kwargs, **guessed)


def _fix_compat_issue29(function):
    #
    # TODO: remove before 1.0 release (will break backwards compatibility)
    #
    if getattr(function, ATTR_EXPECTS_NAMESPACE_OBJECT, False):
        # a modern decorator is used, no compatibility issues
        return function

    if getattr(function, ATTR_INFER_ARGS_FROM_SIGNATURE, False):
        # wrapped in outdated decorator but it implies modern behaviour
        return function

    # Okay, now we've got either a modern-style function (plain signature)
    # or an old-style function which implicitly expects a namespace object.
    # It's very likely that in the latter case the function accepts one and
    # only argument named "args".  If so, we simply wrap this function in
    # @expects_obj and issue a warning.
    spec = get_arg_spec(function)

    if spec.args in [['arg'], ['args'], ['self', 'arg'], ['self', 'args']]:
        # this is it -- a classic old-style function, goddamnit.
        # no checking *args and **kwargs because they are unlikely to matter.
        import warnings
        warnings.warn('Function {0} is very likely to be old-style, i.e. '
                      'implicitly expects a namespace object.  This behaviour '
                      'is deprecated.  Wrap it in @expects_obj decorator or '
                      'convert to plain signature.'.format(function.__name__),
                      DeprecationWarning)
        setattr(function, ATTR_EXPECTS_NAMESPACE_OBJECT, True)
    return function


def _is_positional(args, prefix_chars='-'):
    assert args
    if 1 < len(args) or args[0][0].startswith(tuple(prefix_chars)):
        return False
    else:
        return True


def _get_parser_param_kwargs(parser, argspec):
    argspec = argspec.copy()    # parser methods modify source data
    args = argspec['option_strings']

    if _is_positional(args, prefix_chars=parser.prefix_chars):
        kwargs = parser._get_positional_kwargs(*args, **argspec)
    else:
        kwargs = parser._get_optional_kwargs(*args, **argspec)

    kwargs['dest'] = kwargs['dest'].replace('-', '_')

    return kwargs


def _get_dest(parser, argspec):
    kwargs = _get_parser_param_kwargs(parser, argspec)
    return kwargs['dest']


def set_default_command(parser, function):
    """
    Sets default command (i.e. a function) for given parser.

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
       function signature, `AssemblingError` is raised.

    .. note::

       If the parser was created with ``add_help=True`` (which is by default),
       option name ``-h`` is silently removed from any argument.

    """
    if parser._subparsers:
        raise RuntimeError('Cannot set default command to a parser with '
                           'existing subparsers')

    function = _fix_compat_issue29(function)

    spec = get_arg_spec(function)

    declared_args = getattr(function, ATTR_ARGS, [])
    inferred_args = list(_get_args_from_signature(function))

    if inferred_args and declared_args:
        # We've got a mixture of declared and inferred arguments

        # a mapping of "dest" strings to argument declarations.
        #
        # * a "dest" string is a normalized form of argument name, i.e.:
        #
        #     '-f', '--foo' → 'foo'
        #     'foo-bar'     → 'foo_bar'
        #
        # * argument declaration is a dictionary representing an argument;
        #   it is obtained either from _get_args_from_signature() or from
        #   an @arg decorator (as is).
        #
        dests = OrderedDict()

        for argspec in inferred_args:
            dest = _get_parser_param_kwargs(parser, argspec)['dest']
            dests[dest] = argspec

        for declared_kw in declared_args:
            # an argument is declared via decorator
            dest = _get_dest(parser, declared_kw)
            if dest in dests:
                # the argument is already known from function signature
                #
                # now make sure that this declared arg conforms to the function
                # signature and therefore only refines an inferred arg:
                #
                #      @arg('my-foo')    maps to  func(my_foo)
                #      @arg('--my-bar')  maps to  func(my_bar=...)

                # either both arguments are positional or both are optional
                decl_positional = _is_positional(declared_kw['option_strings'])
                infr_positional = _is_positional(dests[dest]['option_strings'])
                if decl_positional != infr_positional:
                    kinds = {True: 'positional', False: 'optional'}
                    raise AssemblingError(
                        '{func}: argument "{dest}" declared as {kind_i} '
                        '(in function signature) and {kind_d} (via decorator)'
                        .format(
                            func=function.__name__,
                            dest=dest,
                            kind_i=kinds[infr_positional],
                            kind_d=kinds[decl_positional],
                        ))

                # merge explicit argument declaration into the inferred one
                # (e.g. `help=...`)
                dests[dest].update(**declared_kw)
            else:
                # the argument is not in function signature
                varkw = getattr(spec, 'varkw', getattr(spec, 'keywords', []))
                if varkw:
                    # function accepts **kwargs; the argument goes into it
                    dests[dest] = declared_kw
                else:
                    # there's no way we can map the argument declaration
                    # to function signature
                    xs = (dests[x]['option_strings'] for x in dests)
                    raise AssemblingError(
                        '{func}: argument {flags} does not fit '
                        'function signature: {sig}'.format(
                            flags=', '.join(declared_kw['option_strings']),
                            func=function.__name__,
                            sig=', '.join('/'.join(x) for x in xs)))

        # pack the modified data back into a list
        inferred_args = dests.values()

    command_args = inferred_args or declared_args

    # add types, actions, etc. (e.g. default=3 implies type=int)
    command_args = [_guess(x) for x in command_args]

    for draft in command_args:
        draft = draft.copy()
        if 'help' not in draft:
            draft.update(help=DEFAULT_ARGUMENT_TEMPLATE)
        dest_or_opt_strings = draft.pop('option_strings')
        if parser.add_help and '-h' in dest_or_opt_strings:
            dest_or_opt_strings = [x for x in dest_or_opt_strings if x != '-h']
        completer = draft.pop('completer', None)
        try:
            action = parser.add_argument(*dest_or_opt_strings, **draft)
            if COMPLETION_ENABLED and completer:
                action.completer = completer
        except Exception as e:
            raise type(e)('{func}: cannot add arg {args}: {msg}'.format(
                args='/'.join(dest_or_opt_strings), func=function.__name__, msg=e))

    if function.__doc__ and not parser.description:
        parser.description = function.__doc__
    parser.set_defaults(function=function)


def add_commands(parser, functions, namespace=None, title=None,
                 description=None, help=None):
    """
    Adds given functions as commands to given parser.

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

        passed to :meth:`argparse.ArgumentParser.add_subparsers` as `title`.

    :param description:

        passed to :meth:`argparse.ArgumentParser.add_subparsers` as
        `description`.

    :param help:

        passed to :meth:`argparse.ArgumentParser.add_subparsers` as `help`.

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

        parser_kwargs = {

            # add command help from function's docstring
            'help': func.__doc__,

            # set default formatter
            'formatter_class': PARSER_FORMATTER,

        }

        # try adding aliases for command name
        if SUPPORTS_ALIASES:
            parser_kwargs['aliases'] = getattr(func, ATTR_ALIASES, [])

        # create and set up the parser for this command
        command_parser = subparsers.add_parser(cmd_name, **parser_kwargs)
        set_default_command(command_parser, func)
