# -*- coding: utf-8 -*-
"""
Common stuff for tests
~~~~~~~~~~~~~~~~~~~~~~
"""
from argh import ArghParser
from argh.six import  PY3, BytesIO, StringIO, string_types


class DebugArghParser(ArghParser):
    "(does not print stuff to stderr on exit)"

    def exit(self, status=0, message=None):
        raise SystemExit(message)

    def error(self, message):
        self.exit(2, message)


def make_IO():
    "Returns a file object of the same type as `sys.stdout`."
    if PY3:
        return StringIO()
    else:
        return BytesIO()


def call_cmd(parser, command_string, **kwargs):
    if isinstance(command_string, string_types):
        args = command_string.split()
    else:
        args = command_string

    io = make_IO()

    if 'output_file' not in kwargs:
        kwargs['output_file'] = io

    result = parser.dispatch(args, **kwargs)

    if kwargs.get('output_file') is None:
        return result
    else:
        io.seek(0)
        return io.read()


def run(parser, command_string, kwargs=None, exit=False):
    """ Calls the command and returns result.

    If SystemExit is raised, it propagates.

    :exit:
        if set to `True`, then any SystemExit exception is catched and its
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
