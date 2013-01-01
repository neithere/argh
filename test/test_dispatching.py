# -*- coding: utf-8 -*-
"""
Dispatching tests
~~~~~~~~~~~~~~~~~
"""
import argh

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
