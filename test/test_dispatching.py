# coding: utf-8
"""
Dispatching tests
~~~~~~~~~~~~~~~~~
"""
import argh
try:
    from unittest.mock import Mock, patch
except ImportError:
    # FIXME: remove in v.0.28
    from mock import Mock, patch
import pytest

from .base import make_IO


def _dispatch_and_capture(func, command_string, **kwargs):
    if hasattr(command_string, 'split'):
        args = command_string.split()
    else:
        args = command_string

    io = make_IO()
    if 'output_file' not in kwargs:
        kwargs['output_file'] = io

    result = argh.dispatch_command(func, args, **kwargs)

    if kwargs.get('output_file') is None:
        return result
    else:
        io.seek(0)
        return io.read()


def run_func(func, command_string, **kwargs):
    try:
        result = _dispatch_and_capture(func, command_string, **kwargs)
    except SystemExit:
        raise
    else:
        return result


def test_dispatch_command_shortcut():

    def cmd(foo=1):
        return foo

    assert run_func(cmd, '') == '1\n'
    assert run_func(cmd, '--foo 2') == '2\n'


@patch('argh.dispatching.dispatch')
@patch('argh.dispatching.add_commands')
@patch('argparse.ArgumentParser')
def test_entrypoint(ap_cls_mock, add_commands_mock, dispatch_mock):

    entrypoint = argh.EntryPoint('my cool app')

    # no commands

    with pytest.raises(argh.exceptions.DispatchingError) as excinfo:
        entrypoint()
    assert excinfo.exconly().endswith(
        'DispatchingError: no commands for entry point "my cool app"')

    mocked_parser = Mock()
    ap_cls_mock.return_value = mocked_parser

    # a single command

    @entrypoint
    def greet():
        return 'hello'

    entrypoint()

    assert add_commands_mock.called
    add_commands_mock.assert_called_with(mocked_parser, [greet])
    assert dispatch_mock.called
    dispatch_mock.assert_called_with(mocked_parser)

    # multiple commands

    add_commands_mock.reset_mock()
    dispatch_mock.reset_mock()

    @entrypoint
    def hit():
        return 'knight with a chicken'

    entrypoint()

    assert add_commands_mock.called
    add_commands_mock.assert_called_with(mocked_parser, [greet, hit])
    assert dispatch_mock.called
    dispatch_mock.assert_called_with(mocked_parser)
