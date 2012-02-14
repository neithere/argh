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
Helpers
=======
"""
import argparse
import locale
import sys
from types import GeneratorType

from argh.six import b, u, string_types, text_type, BytesIO
from argh.exceptions import CommandError
from argh.utils import get_subparsers
from argh.completion import autocomplete
from argh.constants import (
    ATTR_ALIAS, ATTR_ARGS, ATTR_NO_NAMESPACE, ATTR_WRAPPED_EXCEPTIONS
)


__all__ = [
    'ArghParser', 'add_commands', 'autocomplete', 'dispatch', 'confirm',
    'wrap_errors'
]
def add_commands(parser, functions, namespace=None, title=None,
                 description=None, help=None):
    """Adds given functions as commands to given parser.

    :param parser:

        an :class:`argparse.ArgumentParser` instance.

    :param functions:

        a list of functions. A subparser is created for each of them. If the
        function is decorated with :func:`arg`, the arguments are passed to
        the :class:`~argparse.ArgumentParser.add_argument` method of the
        parser. See also :func:`dispatch` for requirements concerning function
        signatures. The command name is inferred from the function name. Note
        that the underscores in the name are replaced with hyphens, i.e.
        function name "foo_bar" becomes command name "foo-bar".

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
        pretty opaque. You may prefer :class:`ArghParser.add_commands` for a
        bit more predictable API.

    .. admonition:: Design flaw

        This function peeks into the parser object using its internal API.
        Unfortunately the public API does not allow to *get* the subparsers, it
        only lets you *add* them, and do that *once*. So you would have to toss
        the subparsers object around to add something later. That said, I doubt
        that argparse will change a lot in the future as it's already pretty
        stable. If some implementation details would change and break `argh`,
        we'll simply add a workaround a keep it compatibile.

    """
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
        # XXX we could add multiple aliases here but it's a bit of a hack
        cmd_name = getattr(func, ATTR_ALIAS, func.__name__.replace('_','-'))
        cmd_help = func.__doc__
        command_parser = subparsers.add_parser(cmd_name, help=cmd_help)
        for a_args, a_kwargs in getattr(func, ATTR_ARGS, []):
            command_parser.add_argument(*a_args, **a_kwargs)
        command_parser.set_defaults(function=func)

def dispatch(parser, argv=None, add_help_command=True, encoding=None,
             completion=True, pre_call=None, output_file=sys.stdout,
             raw_output=False, namespace=None):
    """Parses given list of arguments using given parser, calls the relevant
    function and prints the result.

    The target function should expect one positional argument: the
    :class:`argparse.Namespace` object. However, if the function is decorated with
    :func:`plain_signature`, the positional and named arguments from the
    namespace object are passed to the function instead of the object itself.

    :param parser:

        the ArgumentParser instance.

    :param argv:

        a list of strings representing the arguments. If `None`, ``sys.argv``
        is used instead. Default is `None`.

    :param add_help_command:

        if `True`, converts first positional argument "help" to a keyword
        argument so that ``help foo`` becomes ``foo --help`` and displays usage
        information for "foo". Default is `True`.

    :param encoding:

        Encoding for results. If `None`, it is determined automatically.
        Default is `None`.

    :param output_file:

        A file-like object for output. If `None`, the resulting lines are
        collected and returned as a string. Default is ``sys.stdout``.

    :param raw_output:

        If `True`, results are written to the output file raw, without adding
        whitespaces or newlines between yielded strings. Default is `False`.

    :param completion:

        If `True`, shell tab completion is enabled. Default is `True`. (You
        will also need to install it.)

    By default the exceptions are not wrapped and will propagate. The only
    exception that is always wrapped is :class:`CommandError` which is
    interpreted as an expected event so the traceback is hidden. You can also
    mark arbitrary exceptions as "wrappable" by using the :func:`wrap_errors`
    decorator.
    """
    if completion:
        autocomplete(parser)

    if argv is None:
        argv = sys.argv[1:]

    if add_help_command:
        if argv and argv[0] == 'help':
            argv.pop(0)
            argv.append('--help')

    # this will raise SystemExit if parsing fails
    args = parser.parse_args(argv, namespace=namespace)

    if hasattr(args, 'function'):
        if pre_call:  # XXX undocumented because I'm unsure if it's OK
            pre_call(args)
        lines = _execute_command(args)
    else:
        # no commands declared, can't dispatch; display help message
        lines = [parser.format_usage()]

    if output_file is None:
        # user wants a string; we create an internal temporary file-like object
        # and will return its contents as a string
        f = BytesIO()
    else:
        # normally this is stdout; can be any file
        f = output_file

    for line in lines:
        # print the line as soon as it is generated to ensure that it is
        # displayed to the user before anything else happens, e.g.
        # raw_input() is called
        output = _encode(line, f, encoding)
        output = '' if output is None else output
        f.write(output)
        if not raw_output:
            # in most cases user wants on message per line
            f.write(b('\n'))

    if output_file is None:
        # user wanted a string; return contents of our temporary file-like obj
        f.seek(0)
        return f.read()

def _encode(line, output_file, encoding=None):
    """Converts given string to given encoding. If no encoding is specified, it
    is determined from terminal settings or, if none, from system settings.
    """
    # Convert string to Unicode
    if not isinstance(line, text_type):
        try:
            line = text_type(line)
        except UnicodeDecodeError:
            line = b(line).decode('utf-8')

    # Choose output encoding
    if not encoding:
        # choose between terminal's and system's preferred encodings
        if output_file.isatty():
            encoding = getattr(output_file, 'encoding', None)
        encoding = encoding or locale.getpreferredencoding()

    # Convert string from Unicode to the output encoding
    return line.encode(encoding)

def _execute_command(args):
    """Asserts that ``args.function`` is present and callable. Tries different
    approaches to calling the function (with an `argparse.Namespace` object or
    with ordinary signature). Yields the results line by line. If CommandError
    is raised, its message is appended to the results (i.e. yielded by the
    generator as a string). All other exceptions propagate unless marked as
    wrappable by :func:`wrap_errors`.
    """
    assert hasattr(args, 'function') and hasattr(args.function, '__call__')

    # the function is nested to catch certain exceptions (see below)
    def _call():
        # Actually call the function
        if getattr(args.function, ATTR_NO_NAMESPACE, False):
            # filter the namespace variables so that only those expected by the
            # actual function will pass
            f = args.function
            if hasattr(f, 'func_code'):
                # Python 2
                expected_args = f.func_code.co_varnames[:f.func_code.co_argcount]
            else:
                # Python 3
                expected_args = f.__code__.co_varnames[:f.__code__.co_argcount]
            ok_args = [x for x in args._get_args() if x in expected_args]
            ok_kwargs = dict((k,v) for k,v in args._get_kwargs()
                             if k in expected_args)
            result = args.function(*ok_args, **ok_kwargs)
        else:
            result = args.function(args)

        # Yield the results
        if isinstance(result, (GeneratorType, list, tuple)):
            # yield each line ASAP, convert CommandError message to a line
            for line in result:
                yield line
        else:
            # yield non-empty non-iterable result as a single line
            if result is not None:
                yield result

    wrappable_exceptions = [CommandError]
    wrappable_exceptions += getattr(args.function, ATTR_WRAPPED_EXCEPTIONS, [])

    try:
        result = _call()
        for line in result:
            yield line
    except tuple(wrappable_exceptions) as e:
        yield text_type(e)


class ArghParser(argparse.ArgumentParser):
    """An :class:`ArgumentParser` suclass which adds a couple of convenience
    methods.

    There is actually no need to subclass the parser. The methods are but
    wrappers for stand-alone functions :func:`add_commands` ,
    :func:`autocomplete` and :func:`dispatch`.
    """
    def add_commands(self, *args, **kwargs):
        "Wrapper for :func:`add_commands`."
        return add_commands(self, *args, **kwargs)

    def autocomplete(self):
        return autocomplete(self)

    def dispatch(self, *args, **kwargs):
        "Wrapper for :func:`dispatch`."
        return dispatch(self, *args, **kwargs)


def confirm(action, default=None, skip=False):
    """A shortcut for typical confirmation prompt.

    :param action:

        a string describing the action, e.g. "Apply changes". A question mark
        will be appended.

    :param default:

        `bool` or `None`. Determines what happens when user hits :kbd:`Enter`
        without typing in a choice. If `True`, default choice is "yes". If
        `False`, it is "no". If `None` the prompt keeps reappearing until user
        types in a choice (not necessarily acceptable) or until the number of
        iteration reaches the limit. Default is `None`.

    :param skip:

        `bool`; if `True`, no interactive prompt is used and default choice is
        returned (useful for batch mode). Default is `False`.

    Usage::

        @arg('key')
        @arg('--silent', help='do not prompt, always give default answers')
        def delete(args):
            item = db.get(Item, args.key)
            if confirm('Delete '+item.title, default=True, skip=args.silent):
                item.delete()
                print('Item deleted.')
            else:
                print('Operation cancelled.')

    Returns `None` on `KeyboardInterrupt` event.
    """
    MAX_ITERATIONS = 3
    if skip:
        return default
    else:
        defaults = {
            None: ('y','n'),
            True: ('Y','n'),
            False: ('y','N'),
        }
        y, n = defaults[default]
        prompt = u('{action}? ({y}/{n})').format(**locals()).encode('utf-8')
        choice = None
        try:
            if default is None:
                cnt = 1
                while not choice and cnt < MAX_ITERATIONS:
                    choice = raw_input(prompt)
                    cnt += 1
            else:
                choice = raw_input(prompt)
        except KeyboardInterrupt:
            return None
    if choice in ('yes', 'y', 'Y'):
        return True
    if choice in ('no', 'n', 'N'):
        return False
    if default is not None:
        return default
    return None

def wrap_errors(*exceptions):
    """Decorator. Wraps given exceptions into :class:`CommandError`. Usage::

        @arg('-x')
        @arg('-y')
        @wrap_errors(AssertionError)
        def foo(args):
            assert args.x or args.y, 'x or y must be specified'

    If the assertion fails, its message will be correctly printed and the
    stack hidden. This helps to avoid boilerplate code.
    """
    def wrapper(func):
        setattr(func, ATTR_WRAPPED_EXCEPTIONS, exceptions)
        return func
    return wrapper
