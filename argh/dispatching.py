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
Dispatching
~~~~~~~~~~~
"""
import argparse
import sys
from types import GeneratorType

from argh import compat, io
from argh.constants import (ATTR_WRAPPED_EXCEPTIONS,
                            ATTR_WRAPPED_EXCEPTIONS_PROCESSOR,
                            ATTR_EXPECTS_NAMESPACE_OBJECT,
                            PARSER_FORMATTER)
from argh.completion import autocomplete
from argh.assembling import add_commands, set_default_command
from argh.exceptions import DispatchingError, CommandError
from argh.utils import get_arg_spec


__all__ = ['dispatch', 'dispatch_command', 'dispatch_commands',
           'PARSER_FORMATTER', 'EntryPoint']


def dispatch(parser, argv=None, add_help_command=True,
             completion=True, pre_call=None,
             output_file=sys.stdout, errors_file=sys.stderr,
             raw_output=False, namespace=None):
    """
    Parses given list of arguments using given parser, calls the relevant
    function and prints the result.

    The target function should expect one positional argument: the
    :class:`argparse.Namespace` object. However, if the function is decorated with
    :func:`~argh.decorators.plain_signature`, the positional and named
    arguments from the namespace object are passed to the function instead
    of the object itself.

    :param parser:

        the ArgumentParser instance.

    :param argv:

        a list of strings representing the arguments. If `None`, ``sys.argv``
        is used instead. Default is `None`.

    :param add_help_command:

        if `True`, converts first positional argument "help" to a keyword
        argument so that ``help foo`` becomes ``foo --help`` and displays usage
        information for "foo". Default is `True`.

    :param output_file:

        A file-like object for output. If `None`, the resulting lines are
        collected and returned as a string. Default is ``sys.stdout``.

    :param errors_file:

        Same as `output_file` but for ``sys.stderr``.

    :param raw_output:

        If `True`, results are written to the output file raw, without adding
        whitespaces or newlines between yielded strings. Default is `False`.

    :param completion:

        If `True`, shell tab completion is enabled. Default is `True`. (You
        will also need to install it.)  See :mod:`argh.completion`.

    By default the exceptions are not wrapped and will propagate. The only
    exception that is always wrapped is :class:`~argh.exceptions.CommandError`
    which is interpreted as an expected event so the traceback is hidden.
    You can also mark arbitrary exceptions as "wrappable" by using the
    :func:`~argh.decorators.wrap_errors` decorator.
    """
    if completion:
        isatty = hasattr(output_file, 'isatty') and output_file.isatty()
        autocomplete(parser, allow_warnings=isatty)

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
            # Actually used in real projects:
            # * https://google.com/search?q=argh+dispatch+pre_call
            # * https://github.com/madjar/aurifere/blob/master/aurifere/cli.py#L92
            pre_call(args)
        lines = _execute_command(args, errors_file)
    else:
        # no commands declared, can't dispatch; display help message
        lines = [parser.format_usage()]

    if output_file is None:
        # user wants a string; we create an internal temporary file-like object
        # and will return its contents as a string
        if sys.version_info < (3,0):
            f = compat.BytesIO()
        else:
            f = compat.StringIO()
    else:
        # normally this is stdout; can be any file
        f = output_file

    for line in lines:
        # print the line as soon as it is generated to ensure that it is
        # displayed to the user before anything else happens, e.g.
        # raw_input() is called

        io.dump(line, f)
        if not raw_output:
            # in most cases user wants on message per line
            io.dump('\n', f)

    if output_file is None:
        # user wanted a string; return contents of our temporary file-like obj
        f.seek(0)
        return f.read()


def _execute_command(args, errors_file):
    """
    Asserts that ``args.function`` is present and callable. Tries different
    approaches to calling the function (with an `argparse.Namespace` object or
    with ordinary signature). Yields the results line by line.

    If :class:`~argh.exceptions.CommandError` is raised, its message is
    appended to the results (i.e. yielded by the generator as a string).
    All other exceptions propagate unless marked as wrappable
    by :func:`wrap_errors`.
    """
    assert hasattr(args, 'function') and hasattr(args.function, '__call__')

    # the function is nested to catch certain exceptions (see below)
    def _call():
        # Actually call the function
        if getattr(args.function, ATTR_EXPECTS_NAMESPACE_OBJECT, False):
            result = args.function(args)
        else:
            # namespace -> dictionary
            _flat_key = lambda key: key.replace('-', '_')
            all_input = dict((_flat_key(k), v) for k,v in  vars(args).items())

            # filter the namespace variables so that only those expected by the
            # actual function will pass

            spec = get_arg_spec(args.function)

            positional = [all_input[k] for k in spec.args]
            kwonly = getattr(spec, 'kwonlyargs', [])
            keywords = dict((k, all_input[k]) for k in kwonly)

            # *args
            if spec.varargs:
                positional += getattr(args, spec.varargs)

            # **kwargs
            varkw = getattr(spec, 'varkw', getattr(spec, 'keywords', []))
            if varkw:
                not_kwargs = ['function'] + spec.args + [spec.varargs] + kwonly
                extra = [k for k in vars(args) if k not in not_kwargs]
                for k in extra:
                    keywords[k] = getattr(args, k)

            result = args.function(*positional, **keywords)

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
        processor = getattr(args.function, ATTR_WRAPPED_EXCEPTIONS_PROCESSOR,
                            lambda e: '{0.__class__.__name__}: {0}'.format(e))

        errors_file.write(compat.text_type(processor(e)))
        errors_file.write('\n')


def dispatch_command(function, *args, **kwargs):
    """
    A wrapper for :func:`dispatch` that creates a one-command parser.
    Uses :attr:`PARSER_FORMATTER`.

    This::

        dispatch_command(foo)

    ...is a shortcut for::

        parser = ArgumentParser()
        set_default_command(parser, foo)
        dispatch(parser)

    This function can be also used as a decorator.
    """
    parser = argparse.ArgumentParser(formatter_class=PARSER_FORMATTER)
    set_default_command(parser, function)
    dispatch(parser, *args, **kwargs)


def dispatch_commands(functions, *args, **kwargs):
    """
    A wrapper for :func:`dispatch` that creates a parser, adds commands to
    the parser and dispatches them.
    Uses :attr:`PARSER_FORMATTER`.

    This::

        dispatch_commands([foo, bar])

    ...is a shortcut for::

        parser = ArgumentParser()
        add_commands(parser, [foo, bar])
        dispatch(parser)

    """
    parser = argparse.ArgumentParser(formatter_class=PARSER_FORMATTER)
    add_commands(parser, functions)
    dispatch(parser, *args, **kwargs)


class EntryPoint(object):
    """
    An object to which functions can be attached and then dispatched.

    When called with an argument, the argument (a function) is registered
    at this entry point as a command.

    When called without an argument, dispatching is triggered with all
    previously registered commands.

    Usage::

        from argh import EntryPoint

        entrypoint = EntryPoint()

        @entrypoint
        def ls():
            for i in range(10):
                print i

        @entrypoint
        def greet():
            print 'hello'

        if __name__ == '__main__':
            entrypoint()

    """
    def __init__(self, name=None):
        self.name = name or 'unnamed'
        self.commands = []

    def __call__(self, f=None):
        if f:
            self._register_command(f)
            return f

        return self._dispatch()

    def _register_command(self, f):
        self.commands.append(f)

    def _dispatch(self):
        if not self.commands:
            raise DispatchingError('no commands for entry point "{0}"'
                                   .format(self.name))

        if len(self.commands) == 1:
            dispatch_command(*self.commands)
        else:
            dispatch_commands(self.commands)
