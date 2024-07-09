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
import re
from typing import Tuple


def get_subparsers(
    parser: argparse.ArgumentParser, create: bool = False
) -> argparse._SubParsersAction:
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

    raise SubparsersNotDefinedError()


def unindent(text: str) -> str:
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


class SubparsersNotDefinedError(Exception): ...


def naive_guess_func_arg_name(option_strings: Tuple[str, ...]) -> str:
    def _opt_to_func_arg_name(opt: str) -> str:
        return opt.strip("-").replace("-", "_")

    if len(option_strings) == 1:
        # the only CLI arg name; adapt and use
        return _opt_to_func_arg_name(option_strings[0])

    are_args_positional = [not arg.startswith("-") for arg in option_strings]

    if any(are_args_positional) and not all(are_args_positional):
        raise MixedPositionalAndOptionalArgsError

    if all(are_args_positional):
        raise TooManyPositionalArgumentNames

    for option_string in option_strings:
        if option_string.startswith("--"):
            # prefixed long; adapt and use
            return _opt_to_func_arg_name(option_string[2:])

    raise CliArgToFuncArgGuessingError(
        f"Unable to convert opt strings {option_strings} to func arg name"
    )


class ArghError(Exception): ...


class CliArgToFuncArgGuessingError(ArghError): ...


class TooManyPositionalArgumentNames(CliArgToFuncArgGuessingError): ...


class MixedPositionalAndOptionalArgsError(CliArgToFuncArgGuessingError): ...
