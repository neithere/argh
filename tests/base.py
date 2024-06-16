"""
Common stuff for tests
~~~~~~~~~~~~~~~~~~~~~~
"""

import io
import os
import sys
from collections import namedtuple

from argh import ArghParser


# hacky constructor for default exit value
def CmdResult(out, err, exit_code=None):
    _CmdResult = namedtuple("CmdResult", ("out", "err", "exit_code"))
    return _CmdResult(out, err, exit_code)


class DebugArghParser(ArghParser):
    "(does not print stuff to stderr on exit)"

    def exit(self, status=0, message=None):
        raise SystemExit(message)

    def error(self, message):
        self.exit(2, message)


def call_cmd(parser, command_string, **kwargs):
    if hasattr(command_string, "split"):
        args = command_string.split()
    else:
        args = command_string

    io_out = io.StringIO()
    io_err = io.StringIO()

    if "output_file" not in kwargs:
        kwargs["output_file"] = io_out
    kwargs["errors_file"] = io_err

    try:
        result = parser.dispatch(args, **kwargs)
    except SystemExit as e:
        result = None
        exit_code = e.code or 0  # e.code may be None
    else:
        exit_code = None

    if kwargs.get("output_file") is None:
        return CmdResult(out=result, err=io_err.read(), exit_code=exit_code)

    io_out.seek(0)
    io_err.seek(0)
    return CmdResult(out=io_out.read(), err=io_err.read(), exit_code=exit_code)


def run(parser, command_string, kwargs=None, exit=False):
    """Calls the command and returns CmdResult(out, err, exit status),
    with exit status None if no SystemExit was raised.

    :exit:
        if set to `True` and a SystemExit is raised, the status code is returned;
        if the exception is not raised, an AssertionError is raised.

    """
    kwargs = kwargs or {}
    result = call_cmd(parser, command_string, **kwargs)
    if exit:
        if result.exit_code is None:
            raise AssertionError("Did not exit")
        return result.exit_code
    return result


def get_usage_string(definitions="{cmd} ..."):
    prog = os.path.basename(sys.argv[0])
    return "usage: " + prog + " [-h] " + definitions + "\n\n"
