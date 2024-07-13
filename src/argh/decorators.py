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
Command decorators
~~~~~~~~~~~~~~~~~~
"""

from typing import Callable, List, Optional, Type


from argh.constants import (
    ATTR_ALIASES,
    ATTR_ARGS,
    ATTR_NAME,
    ATTR_WRAPPED_EXCEPTIONS,
    ATTR_WRAPPED_EXCEPTIONS_PROCESSOR,
)
from argh.dto import ParserAddArgumentSpec
from argh.utils import CliArgToFuncArgGuessingError, naive_guess_func_arg_name

__all__ = ["aliases", "named", "arg", "wrap_errors"]


def named(new_name: str) -> Callable:
    """
    Sets given string as command name instead of the function name.
    The string is used verbatim without further processing.

    Usage::

        @named("load")
        def do_load_some_stuff_and_keep_the_original_function_name(args):
            ...

    The resulting command will be available only as ``load``.  To add aliases
    without renaming the command, check :func:`aliases`.

    .. versionadded:: 0.19
    """

    def wrapper(func: Callable) -> Callable:
        setattr(func, ATTR_NAME, new_name)
        return func

    return wrapper


def aliases(*names: List[str]) -> Callable:
    """
    Defines alternative command name(s) for given function (along with its
    original name). Usage::

        @aliases("co", "check")
        def checkout(args):
            ...

    The resulting command will be available as ``checkout``, ``check`` and ``co``.

    .. versionadded:: 0.19
    """

    def wrapper(func: Callable) -> Callable:
        setattr(func, ATTR_ALIASES, names)
        return func

    return wrapper


def arg(*args: str, **kwargs) -> Callable:
    """
    Declares an argument for given function. Does not register the function
    anywhere, nor does it modify the function in any way.

    The signature of the decorator matches that of
    :meth:`argparse.ArgumentParser.add_argument`, only some keywords are not
    required if they can be easily guessed (e.g. you don't have to specify type
    or action when an `int` or `bool` default value is supplied).

    .. note::

        `completer` is an exception; it's not accepted by
        `add_argument()` but instead meant to be assigned to the
        action returned by that method, see
        https://kislyuk.github.io/argcomplete/#specifying-completers
        for details.

    Typical use case: in combination with ordinary function signatures to add
    details that cannot be expressed with that syntax (e.g. help message).

    Usage::

        from argh import arg

        @arg("path", help="path to the file to load")
        @arg("--format", choices=["yaml","json"])
        @arg("-v", "--verbosity", choices=range(0,3), default=2)
        def load(
            path: str,
            something: str | None = None,
            format: str = "json",
            dry_run: bool = False,
            verbosity: int = 1
        ) -> None:
            loaders = {"json": json.load, "yaml": yaml.load}
            loader = loaders[args.format]
            data = loader(args.path)
            if not args.dry_run:
                if verbosity < 1:
                    print("saving to the database")
                put_to_database(data)

    In this example:

    - `path` declaration is extended with `help`;
    - `format` declaration is extended with `choices`;
    - `dry_run` declaration is not duplicated;
    - `verbosity` is extended with `choices` and the default value is
      overridden.  (If both function signature and `@arg` define a default
      value for an argument, `@arg` wins.)

    .. note::

        It is recommended to avoid using this decorator unless there's no way
        to tune the argument's behaviour or presentation using ordinary
        function signatures.  Readability counts, don't repeat yourself.

        The decorator is likely to be deprecated in the upcoming versions
        of Argh in favour of typing hints; see :doc:`the_story`.

    """

    def wrapper(func: Callable) -> Callable:
        if not args:
            raise CliArgToFuncArgGuessingError("at least one CLI arg must be defined")

        if "dest" in kwargs:
            func_arg_name = kwargs.pop("dest")
        else:
            func_arg_name = naive_guess_func_arg_name(args)

        cli_arg_names = [name.replace("_", "-") for name in args]
        completer = kwargs.pop("completer", None)
        spec = ParserAddArgumentSpec.make_from_kwargs(
            func_arg_name=func_arg_name,
            cli_arg_names=cli_arg_names,
            parser_add_argument_kwargs=kwargs,
        )
        if completer:
            spec.completer = completer

        declared_args = getattr(func, ATTR_ARGS, [])
        # The innermost decorator is called first but appears last in the code.
        # We need to preserve the expected order of positional arguments, so
        # the outermost decorator inserts its value before the innermost's:
        declared_args.insert(0, spec)
        setattr(func, ATTR_ARGS, declared_args)
        return func

    return wrapper


def wrap_errors(
    errors: Optional[List[Type[Exception]]] = None,
    processor: Optional[Callable] = None,
    *args,
) -> Callable:
    """
    Decorator. Wraps given exceptions into
    :class:`~argh.exceptions.CommandError`. Usage::

        @wrap_errors([AssertionError])
        def foo(x=None, y=None):
            assert x or y, "x or y must be specified"

    If the assertion fails, its message will be correctly printed and the
    stack hidden. This helps to avoid boilerplate code.

    :param errors:
        A list of exception classes to catch.
    :param processor:
        A callable that expects the exception object and returns a string.
        For example, this renders all wrapped errors in red colour::

            from termcolor import colored

            def failure(err):
                return colored(str(err), "red")

            @wrap_errors(processor=failure)
            def my_command(...):
                ...

    """

    def wrapper(func: Callable):
        if errors:
            setattr(func, ATTR_WRAPPED_EXCEPTIONS, errors)

        if processor:
            setattr(func, ATTR_WRAPPED_EXCEPTIONS_PROCESSOR, processor)

        return func

    return wrapper
