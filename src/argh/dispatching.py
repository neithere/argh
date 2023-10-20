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
Dispatching
~~~~~~~~~~~
"""
import argparse
import io
import sys
import warnings
from types import GeneratorType
from typing import IO, Any, Callable, Dict, Iterator, List, Optional, Tuple

from argh.assembling import add_commands, set_default_command
from argh.completion import autocomplete
from argh.constants import (
    ATTR_EXPECTS_NAMESPACE_OBJECT,
    ATTR_WRAPPED_EXCEPTIONS,
    ATTR_WRAPPED_EXCEPTIONS_PROCESSOR,
    DEST_FUNCTION,
    PARSER_FORMATTER,
)
from argh.exceptions import CommandError, DispatchingError
from argh.utils import get_arg_spec

__all__ = [
    "ArghNamespace",
    "dispatch",
    "dispatch_command",
    "dispatch_commands",
    "parse_and_resolve",
    "run_endpoint_function",
    "PARSER_FORMATTER",
    "EntryPoint",
]


class ArghNamespace(argparse.Namespace):
    """
    A namespace object which collects the stack of functions.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._functions_stack: List[Callable] = []

    def __setattr__(self, key: str, value: Any) -> None:
        if key == DEST_FUNCTION:
            # don't register the function under DEST_FUNCTION name.
            # If `ArgumentParser.parse_known_args()` sees that we already have
            # such attribute, it skips it.  However, it goes from the topmost
            # parser to subparsers.  We need the function mapped to the
            # subparser.  So we fool the `ArgumentParser` and pretend that we
            # didn't get a DEST_FUNCTION attribute; however, in fact we collect
            # all its values in a stack.  The last item in the stack would be
            # the function mapped to the innermost parser — the one we need.
            self._functions_stack.append(value)
        else:
            super().__setattr__(key, value)

    def get_function(self) -> Callable:
        return self._functions_stack[-1]


def dispatch(
    parser: argparse.ArgumentParser,
    argv: Optional[List[str]] = None,
    add_help_command: bool = False,
    completion: bool = True,
    output_file: IO = sys.stdout,
    errors_file: IO = sys.stderr,
    raw_output: bool = False,
    namespace: Optional[argparse.Namespace] = None,
    skip_unknown_args: bool = False,
) -> Optional[str]:
    """
    Parses given list of arguments using given parser, calls the relevant
    function and prints the result.

    Internally calls :func:`~argh.dispatching.parse_and_resolve` and then
    :func:`~argh.dispatching.run_endpoint_function`.

    :param parser:

        the ArgumentParser instance.

    :param argv:

        a list of strings representing the arguments. If `None`, ``sys.argv``
        is used instead. Default is `None`.

    :param add_help_command:

        if `True`, converts first positional argument "help" to a keyword
        argument so that ``help foo`` becomes ``foo --help`` and displays usage
        information for "foo". Default is `False`.

        .. versionchanged:: 0.30

           The default value is now ``False`` instead of ``True``.

        .. deprecated:: 0.30

           This argument will be removed in v.0.31.  The user is expected to
           use ``--help`` instead of ``help``.

    :param output_file:

        A file-like object for output. If `None`, the resulting lines are
        collected and returned as a string. Default is ``sys.stdout``.

    :param errors_file:

        Same as `output_file` but for ``sys.stderr``, and `None` is not accepted.

    :param raw_output:

        If `True`, results are written to the output file raw, without adding
        whitespaces or newlines between yielded strings. Default is `False`.

    :param completion:

        If `True`, shell tab completion is enabled. Default is `True`. (You
        will also need to install it.)  See :mod:`argh.completion`.

    :param skip_unknown_args:

        If `True`, unknown arguments do not cause an error
        (`ArgumentParser.parse_known_args` is used).

    :param namespace:

        An `argparse.Namespace`-like object.  By default an
        :class:`argh.dispatching.ArghNamespace` object is used.  Please note
        that support for combined default and nested functions may be broken
        if a different type of object is forced.

    By default the exceptions are not wrapped and will propagate. The only
    exception that is always wrapped is :class:`~argh.exceptions.CommandError`
    which is interpreted as an expected event so the traceback is hidden.
    You can also mark arbitrary exceptions as "wrappable" by using the
    :func:`~argh.decorators.wrap_errors` decorator.

    Wrapped exceptions, or other "expected errors" like parse failures,
    will cause a SystemExit to be raised.
    """

    # TODO: remove in v0.31+/v1.0
    if add_help_command:  # pragma: nocover
        warnings.warn(
            DeprecationWarning(
                "The argument `add_help_command` in `dispatch()` is deprecated. "
                "The user is expected to type `--help` instead of `help`."
            )
        )
        if argv and argv[0] == "help":
            argv.pop(0)
            argv.append("--help")

    endpoint_function, namespace_obj = parse_and_resolve(
        parser=parser,
        completion=completion,
        argv=argv,
        namespace=namespace,
        skip_unknown_args=skip_unknown_args,
    )

    if not endpoint_function:
        parser.print_usage(output_file)
        return None

    return run_endpoint_function(
        function=endpoint_function,
        namespace_obj=namespace_obj,
        output_file=output_file,
        errors_file=errors_file,
        raw_output=raw_output,
    )


def parse_and_resolve(
    parser: argparse.ArgumentParser,
    argv: Optional[List[str]] = None,
    completion: bool = True,
    namespace: Optional[argparse.Namespace] = None,
    skip_unknown_args: bool = False,
) -> Tuple[Optional[Callable], argparse.Namespace]:
    """
    .. versionadded:: 0.30

    Parses CLI arguments and resolves the endpoint function.
    """
    if completion:
        autocomplete(parser)

    if argv is None:
        argv = sys.argv[1:]

    if not namespace:
        namespace = ArghNamespace()

    # this will raise SystemExit if parsing fails
    if skip_unknown_args:
        namespace_obj, unknown_args = parser.parse_known_args(argv, namespace=namespace)
        # store unknown args on the namespace
        namespace_obj._unknown_args = unknown_args
    else:
        namespace_obj = parser.parse_args(argv, namespace=namespace)

    function = _get_function_from_namespace_obj(namespace_obj)

    return function, namespace_obj


def run_endpoint_function(
    function: Callable,
    namespace_obj: argparse.Namespace,
    output_file: IO = sys.stdout,
    errors_file: IO = sys.stderr,
    raw_output: bool = False,
) -> Optional[str]:
    """
    .. versionadded:: 0.30

    Extracts arguments from the namespace object, calls the endpoint function
    and processes its output.
    """
    lines = _execute_command(function, namespace_obj, errors_file)

    return _process_command_output(lines, output_file, raw_output)


def _process_command_output(
    lines: Iterator[str], output_file: Optional[IO], raw_output: bool
) -> Optional[str]:
    out_io: IO

    if output_file is None:
        # user wants a string; we create an internal temporary file-like object
        # and will return its contents as a string
        out_io = io.StringIO()
    else:
        # normally this is stdout; can be any file
        out_io = output_file

    # this may raise user exceptions, or SystemExit for wrapped exceptions
    for line in lines:
        # print the line as soon as it is generated to ensure that it is
        # displayed to the user before anything else happens, e.g.
        # raw_input() is called
        out_io.write(str(line))
        if not raw_output:
            # in most cases user wants one message per line
            out_io.write("\n")

    if output_file is None:
        # user wanted a string; return contents of our temporary file-like obj
        out_io.seek(0)
        return out_io.read()

    return None


def _get_function_from_namespace_obj(
    namespace_obj: argparse.Namespace,
) -> Optional[Callable]:
    if isinstance(namespace_obj, ArghNamespace):
        # our special namespace object keeps the stack of assigned functions
        try:
            function = namespace_obj.get_function()
        except (AttributeError, IndexError):
            return None
    else:
        # a custom (probably vanilla) namespace object keeps the last assigned
        # function; this may be wrong but at least something may work
        if not hasattr(namespace_obj, DEST_FUNCTION):
            return None
        function = getattr(namespace_obj, DEST_FUNCTION)

    if not hasattr(function, "__call__"):
        return None

    return function


def _execute_command(
    function: Callable, namespace_obj: argparse.Namespace, errors_file: IO
) -> Iterator[str]:
    """
    Assumes that `function` is a callable.  Tries different approaches
    to call it (with `namespace_obj` or with ordinary signature).
    Yields the results line by line.

    If :class:`~argh.exceptions.CommandError` is raised, its message is
    written to the error file, and a SystemExit is raised.
    All other exceptions propagate unless marked as wrappable
    by :func:`wrap_errors`.
    """

    # the function is nested to catch certain exceptions (see below)
    def _call():
        # Actually call the function
        if getattr(function, ATTR_EXPECTS_NAMESPACE_OBJECT, False):
            result = function(namespace_obj)
        else:
            # namespace -> dictionary
            def _flat_key(key):
                return key.replace("-", "_")

            all_input = dict((_flat_key(k), v) for k, v in vars(namespace_obj).items())

            # filter the namespace variables so that only those expected
            # by the actual function will pass

            spec = get_arg_spec(function)

            positional = [all_input[k] for k in spec.args]
            kwonly = getattr(spec, "kwonlyargs", [])
            keywords = dict((k, all_input[k]) for k in kwonly)

            # *args
            if spec.varargs:
                positional += all_input[spec.varargs]

            # **kwargs
            varkw = getattr(spec, "varkw", getattr(spec, "keywords", []))
            if varkw:
                not_kwargs = [DEST_FUNCTION] + spec.args + [spec.varargs] + kwonly
                for k in vars(namespace_obj):
                    normalized_k = _flat_key(k)
                    if k.startswith("_") or normalized_k in not_kwargs:
                        continue
                    keywords[normalized_k] = getattr(namespace_obj, k)

            result = function(*positional, **keywords)

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
    wrappable_exceptions += getattr(function, ATTR_WRAPPED_EXCEPTIONS, [])

    def default_exception_processor(exc: Exception) -> str:
        return f"{exc.__class__.__name__}: {exc}"

    try:
        result = _call()
        for line in result:
            yield line
    except tuple(wrappable_exceptions) as exc:
        processor = getattr(
            function, ATTR_WRAPPED_EXCEPTIONS_PROCESSOR, default_exception_processor
        )

        errors_file.write(str(processor(exc)))
        errors_file.write("\n")

        # Use code from CommandError if available, otherwise default to 1
        code = exc.code if isinstance(exc, CommandError) and exc.code is not None else 1

        sys.exit(code)


def dispatch_command(function: Callable, *args, **kwargs) -> None:
    """
    A wrapper for :func:`dispatch` that creates a one-command parser.
    Uses :attr:`argh.constants.PARSER_FORMATTER`.

    This::

        dispatch_command(foo)

    ...is a shortcut for::

        parser = ArgumentParser()
        set_default_command(parser, foo)
        dispatch(parser)

    This function can be also used as a decorator::

        @dispatch_command
        def main(foo: int = 123) -> int:
            return foo + 1

    """
    parser = argparse.ArgumentParser(formatter_class=PARSER_FORMATTER)
    set_default_command(parser, function)
    dispatch(parser, *args, **kwargs)


def dispatch_commands(functions: List[Callable], *args, **kwargs) -> None:
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


class EntryPoint:
    """
    An object to which functions can be attached and then dispatched.

    When called with an argument, the argument (a function) is registered
    at this entry point as a command.

    When called without an argument, dispatching is triggered with all
    previously registered commands.

    Usage::

        from argh import EntryPoint

        app = EntryPoint("main", dict(description="This is a cool app"))

        @app
        def ls() -> None:
            for i in range(10):
                print i

        @app
        def greet() -> None:
            print "hello"

        if __name__ == "__main__":
            app()

    """

    def __init__(
        self, name: Optional[str] = None, parser_kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        self.name = name or "unnamed"
        self.commands: List[Callable] = []
        self.parser_kwargs = parser_kwargs or {}

    def __call__(self, function: Optional[Callable] = None):
        if function:
            self._register_command(function)
            return function

        return self._dispatch()

    def _register_command(self, function: Callable) -> None:
        self.commands.append(function)

    def _dispatch(self) -> None:
        if not self.commands:
            raise DispatchingError(f'no commands for entry point "{self.name}"')

        parser = argparse.ArgumentParser(**self.parser_kwargs)
        add_commands(parser, self.commands)
        dispatch(parser)
