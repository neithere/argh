# -*- coding: utf-8 -*-
"""
Common stuff for tests
~~~~~~~~~~~~~~~~~~~~~~
"""
import re

import pytest

from argh import ArghParser
from argh.six import (
    PY3, BytesIO, StringIO, u, string_types, text_type, binary_type,
    iteritems
)


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

def assert_cmd_returns(parser, command_string, expected_result, **kwargs):
    """Executes given command using given parser and asserts that it prints
    given value.
    """
    result = run(parser, command_string, **kwargs)
    if isinstance(expected_result, re._pattern_type):
        assert expected_result.match(result), \
            '/{0}/ !~ {1!r}'.format(expected_result.pattern, result)
    else:
        assert expected_result == result


def assert_cmd_regex(parser, command_string, pattern, **kwargs):
    return assert_cmd_returns(parser, command_string, re.compile(pattern),
                              **kwargs)


def assert_cmd_exits(parser, command_string, message_regex=''):
    "When a command forces exit, it *may* fail, but may just print help."
    with pytest.raises(SystemExit) as excinfo:
        parser.dispatch(command_string.split())
    assert re.match(message_regex, text_type(excinfo.value)), \
        '/{0}/ vs {1!r}'.format(message_regex, str(excinfo.value))


def assert_cmd_fails(parser, command_string, message_regex):
    "exists with a message = fails"
    assert message_regex
    assert_cmd_exits(parser, command_string, message_regex)


def assert_cmd_doesnt_fail(parser, command_string):
    """(for cases when a commands doesn't fail but also (maybe) doesn't
    return results and just prints them.)
    """
    assert_cmd_exits(parser, command_string)


class BaseArghTestCase(object):
    commands = {}

    def setup_method(self, method):
        self.parser = DebugArghParser('PROG')
        for namespace, commands in iteritems(self.commands):
            self.parser.add_commands(commands, namespace=namespace)

    def _call_cmd(self, *args, **kwargs):
        return call_cmd(self.parser, *args, **kwargs)

    def assert_cmd_returns(self, *args, **kwargs):
        return assert_cmd_returns(self.parser, *args, **kwargs)

    def assert_cmd_regex(self, *args, **kwargs):
        return assert_cmd_regex(self.parser, *args, **kwargs)

    def assert_cmd_exits(self, *args, **kwargs):
        assert_cmd_exits(self.parser, *args, **kwargs)

    def assert_cmd_fails(self, *args, **kwargs):
        return assert_cmd_fails(self.parser, *args, **kwargs)

    def assert_cmd_doesnt_fail(self, *args, **kwargs):
        return assert_cmd_doesnt_fail(self.parser, *args, **kwargs)
