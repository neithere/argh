# coding: utf-8
"""
Common stuff for tests
~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import sys
from collections import namedtuple

from argh import ArghParser
from argh.compat import BytesIO, StringIO


CmdResult = namedtuple('CmdResult', ('out', 'err'))


class DebugArghParser(ArghParser):
    "(does not print stuff to stderr on exit)"

    def exit(self, status=0, message=None):
        raise SystemExit(message)

    def error(self, message):
        self.exit(2, message)


def make_IO():
    "Returns a file object of the same type as `sys.stdout`."
    if sys.version_info < (3,0):
        return BytesIO()
    else:
        return StringIO()


def call_cmd(parser, command_string, **kwargs):
    if hasattr(command_string, 'split'):
        args = command_string.split()
    else:
        args = command_string

    io_out = make_IO()
    io_err = make_IO()

    if 'output_file' not in kwargs:
        kwargs['output_file'] = io_out
    kwargs['errors_file'] = io_err

    result = parser.dispatch(args, **kwargs)

    if kwargs.get('output_file') is None:
        return CmdResult(out=result, err=io_err.read())
    else:
        io_out.seek(0)
        io_err.seek(0)
        return CmdResult(out=io_out.read(), err=io_err.read())


def run(parser, command_string, kwargs=None, exit=False):
    """ Calls the command and returns result.

    If SystemExit is raised, it propagates.

    :exit:
        if set to `True`, then any SystemExit exception is caught and its
        string representation is returned; if the exception is not raised,
        an AssertionError is raised.  In other words, this parameter inverts
        the function's behaviour and expects SystemExit as the correct event.

    """
    kwargs = kwargs or {}
    try:
        return call_cmd(parser, command_string, **kwargs)
    except SystemExit as error:
        if exit:
            if error.args == (None,):
                return None
            else:
                return str(error)
        else:
            raise
    else:
        if exit:
            raise AssertionError('Did not exit')


def get_usage_string(definitions='{cmd} ...'):
    prog = os.path.basename(sys.argv[0])
    return 'usage: ' + prog + ' [-h] ' + definitions + '\n\n'
