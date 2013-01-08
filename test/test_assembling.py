# -*- coding: utf-8 -*-
"""
Unit Tests For Assembling Phase
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import sys
import mock
import pytest

import argh


def test_guess_type_from_choices():
    old = dict(option_strings=('foo',), choices=[1,2])
    new = dict(option_strings=('foo',), choices=[1,2], type=int)
    assert new == argh.assembling._guess(old)

    # ensure no overrides
    same = dict(option_strings=('foo',), choices=[1,2], type='NO_MATTER_WHAT')
    assert same == argh.assembling._guess(same)


def test_guess_type_from_default():
    old = dict(option_strings=('foo',), default=1)
    new = dict(option_strings=('foo',), default=1, type=int)
    assert new == argh.assembling._guess(old)

    # ensure no overrides
    same = dict(option_strings=('foo',), default=1, type='NO_MATTER_WHAT')
    assert same == argh.assembling._guess(same)


def test_guess_action_from_default():
    # True → store_false
    old = dict(option_strings=('foo',), default=False)
    new = dict(option_strings=('foo',), default=False, action='store_true')
    assert new == argh.assembling._guess(old)

    # True → store_false
    old = dict(option_strings=('foo',), default=True)
    new = dict(option_strings=('foo',), default=True, action='store_false')
    assert new == argh.assembling._guess(old)

    # ensure no overrides
    same = dict(option_strings=('foo',), default=False, action='NO_MATTER_WHAT')
    assert same == argh.assembling._guess(same)


def test_set_default_command():

    def func():
        pass

    setattr(func, argh.constants.ATTR_ARGS, (
        dict(option_strings=('foo',), nargs='+', choices=[1,2], help='me'),
        dict(option_strings=('-b', '--bar',), default=False),
    ))

    parser = argh.ArghParser()

    parser.add_argument = mock.MagicMock()
    parser.set_defaults = mock.MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        mock.call('foo', nargs='+', choices=[1,2], help='me', type=int),
        mock.call('-b', '--bar', default=False, action='store_true')
    ]
    assert parser.set_defaults.mock_calls == [
        mock.call(function=func)
    ]


def test_set_default_command_docstring():

    def func():
        "docstring"
        pass

    parser = argh.ArghParser()

    argh.set_default_command(parser, func)

    assert parser.description == 'docstring'


def test_set_default_command_vs_multiple():

    def one(): return 1
    def two(): return 2

    p = argh.ArghParser()
    p.set_default_command(one)

    with pytest.raises(RuntimeError) as excinfo:
        p.add_commands([two])
    msg = 'Cannot add commands to a single-command parser'
    assert msg == str(excinfo.value)


def test_set_default_command_vs_subparsers():

    def one(): return 1
    def two(): return 2

    p = argh.ArghParser()
    p.add_commands([one])

    with pytest.raises(RuntimeError) as excinfo:
        p.set_default_command(two)
    msg = 'Cannot set default command to a parser with existing subparsers'
    assert msg == str(excinfo.value)


def test_set_default_command_mixed_arg_types():

    def func():
        pass

    setattr(func, argh.constants.ATTR_ARGS, [
        dict(option_strings=('x','--y'))
    ])

    p = argh.ArghParser()

    with pytest.raises(ValueError) as excinfo:
        p.set_default_command(func)
    msg = "func: cannot add arg x/--y: invalid option string"
    assert msg in str(excinfo.value)


def test_set_default_command_varargs():

    def func(*file_paths):
        yield ', '.join(file_paths)

    parser = argh.ArghParser()

    parser.add_argument = mock.MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        mock.call('file_paths', nargs='*'),
    ]


def test_set_default_command_kwargs():

    @argh.arg('foo')
    @argh.arg('--bar')
    def func(x, **kwargs):
        pass

    parser = argh.ArghParser()

    parser.add_argument = mock.MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        mock.call('x'),
        mock.call('foo'),
        mock.call('--bar'),
    ]


def test_annotation():
    "Extracting argument help from function annotations (Python 3 only)."
    if sys.version_info < (3,0):
        pytest.skip('unsupported configuration')

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


@mock.patch('argh.assembling.COMPLETION_ENABLED', True)
def test_custom_argument_completer():
    "Issue #33: Enable custom per-argument shell completion"

    def func(foo):
        pass

    setattr(func, argh.constants.ATTR_ARGS, [
        dict(option_strings=('foo',), completer='STUB')
    ])

    p = argh.ArghParser()
    p.set_default_command(func)

    assert p._actions[-1].completer == 'STUB'


@mock.patch('argh.assembling.COMPLETION_ENABLED', False)
def test_custom_argument_completer_no_backend():
    "If completion backend is not available, nothing breaks"

    def func(foo):
        pass

    setattr(func, argh.constants.ATTR_ARGS, [
        dict(option_strings=('foo',), completer='STUB')
    ])

    p = argh.ArghParser()
    p.set_default_command(func)

    assert not hasattr(p._actions[-1], 'completer')
