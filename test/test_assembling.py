# -*- coding: utf-8 -*-
"""
Assembling Tests
~~~~~~~~~~~~~~~~
"""
import re

import pytest

import argh

from .base import DebugArghParser, run


def test_default_command():
    @argh.arg('--foo', default=1)
    def cmd(args):
        return args.foo

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == '1\n'
    assert run(p, '--foo 2') == '2\n'
    assert run(p, '--help', exit=True)


def test_default_command_vs_multiple():
    def one(args): return 1
    def two(args): return 2

    p = DebugArghParser('PROG')
    p.set_default_command(one)

    with pytest.raises(RuntimeError) as excinfo:
        p.add_commands([two])
    msg = 'Cannot add commands to a single-command parser'
    assert msg == str(excinfo.value)


def test_default_command_vs_subparsers():
    def one(args): return 1
    def two(args): return 2

    p = DebugArghParser('PROG')
    p.add_commands([one])

    with pytest.raises(RuntimeError) as excinfo:
        p.set_default_command(two)
    msg = 'Cannot set default command to a parser with existing subparsers'
    assert msg == str(excinfo.value)


def test_command_decorator():
    """The @command decorator creates arguments from function signature.
    """
    @argh.arg('x', '--y')
    def cmd(args):
        return

    p = DebugArghParser()

    with pytest.raises(ValueError) as excinfo:
        p.set_default_command(cmd)
    msg = "cmd: cannot add arg x/--y: invalid option string"
    assert msg in str(excinfo.value)


def test_annotation():
    "Extracting argument help from function annotations (Python 3 only)."
    if argh.six.PY3:
        # Yes, this looks horrible, but otherwise Python 2 would die
        # screaming and cursing as it is completely in the dark about the
        # sweetness of annotations and we can but tolerate its ignorance.
        ns = {}
        exec("def cmd(foo : 'quux' = 123):\n    'bar'\npass", None, ns)
        cmd = ns['cmd']
        p = argh.ArghParser()
        p.set_default_command(argh.command(cmd))
        prog_help = p.format_help()
        assert 'quux' in prog_help
