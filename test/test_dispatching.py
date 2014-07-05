# coding: utf-8
"""
Dispatching tests
~~~~~~~~~~~~~~~~~
"""
import argh
from mock import patch
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

    @argh.arg('--foo', default=1)
    def cmd(args):
        return args.foo

    assert run_func(cmd, '') == '1\n'
    assert run_func(cmd, '--foo 2') == '2\n'


@patch('argh.dispatching.dispatch_command')
@patch('argh.dispatching.dispatch_commands')
def test_entrypoint(dcs_mock, dc_mock):

    entrypoint = argh.EntryPoint('my cool app')

    # no commands

    with pytest.raises(argh.exceptions.DispatchingError) as excinfo:
        entrypoint()
    assert excinfo.exconly().endswith(
        'DispatchingError: no commands for entry point "my cool app"')

    # a single command

    @entrypoint
    def greet():
        return 'hello'

    entrypoint()
    assert not dcs_mock.called
    assert dc_mock.called
    dc_mock.assert_called_with(greet)

    # multiple commands

    @entrypoint
    def hit():
        return 'knight with a chicken'

    entrypoint()
    dcs_mock.assert_called_with([greet, hit])
