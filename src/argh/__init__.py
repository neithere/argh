"""
Argh
~~~~
"""

#
#  Copyright © 2010—2023 Andrey Mikhaylenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README.rst for copying conditions.
#
from .assembling import add_commands, add_subcommands, set_default_command
from .decorators import aliases, arg, named, wrap_errors
from .dispatching import (
    PARSER_FORMATTER,
    ArghNamespace,
    EntryPoint,
    dispatch,
    dispatch_command,
    dispatch_commands,
    parse_and_resolve,
    run_endpoint_function,
)
from .exceptions import AssemblingError, CommandError, DispatchingError
from .helpers import ArghParser
from .interaction import confirm

__all__ = (
    "add_commands",
    "add_subcommands",
    "set_default_command",
    "aliases",
    "arg",
    "named",
    "wrap_errors",
    "PARSER_FORMATTER",
    "ArghNamespace",
    "EntryPoint",
    "dispatch",
    "dispatch_command",
    "dispatch_commands",
    "AssemblingError",
    "CommandError",
    "DispatchingError",
    "ArghParser",
    "confirm",
    "parse_and_resolve",
    "run_endpoint_function",
)
