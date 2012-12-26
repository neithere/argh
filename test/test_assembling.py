# -*- coding: utf-8 -*-
"""
Assembling Tests
~~~~~~~~~~~~~~~~
"""
import mock
import pytest

import argh
from argh.utils import Arg

from .base import DebugArghParser, run

#------------------------------------------------------------------------------
#
# UNIT TESTS
#

def test_guess_type_from_choices():
    old = Arg(('foo',), {'choices': [1,2]})
    new = Arg(('foo',), {'choices': [1,2], 'type': int})
    assert new == argh.assembling._guess(old)

    # ensure no overrides
    same = Arg(('foo',), {'choices': [1,2], 'type': 'NO_MATTER_WHAT'})
    assert same == argh.assembling._guess(same)


def test_guess_type_from_default():
    old = Arg(('foo',), {'default': 1})
    new = Arg(('foo',), {'default': 1, 'type': int})
    assert new == argh.assembling._guess(old)

    # ensure no overrides
    same = Arg(('foo',), {'default': '1', 'type': 'NO_MATTER_WHAT'})
    assert same == argh.assembling._guess(same)


def test_guess_action_from_default():
    # True → store_false
    old = Arg(('foo',), {'default': False})
    new = Arg(('foo',), {'default': False, 'action': 'store_true'})
    assert new == argh.assembling._guess(old)

    # True → store_false
    old = Arg(('foo',), {'default': True})
    new = Arg(('foo',), {'default': True, 'action': 'store_false'})
    assert new == argh.assembling._guess(old)

    # ensure no overrides
    same = Arg(('foo',), {'default': False, 'action': 'NO_MATTER_WHAT'})
    assert same == argh.assembling._guess(same)


def test_set_default_command():
    def func():
        pass

    setattr(func, argh.constants.ATTR_ARGS, (
        Arg(('foo',), dict(nargs='+', choices=[1,2], help='me')),
        Arg(('-b', '--bar',), dict(default=False)),
    ))

    parser = argh.ArghParser()

    parser.add_argument = mock.MagicMock()
    parser.set_defaults = mock.MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        mock.call('foo', nargs='+', choices=[1,2], help='me', type=int),
        mock.call('-b', '--bar', default=False, action='store_true')
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

    setattr(func, argh.constants.ATTR_ARGS, [Arg(('x','--y'), {})])

    p = argh.ArghParser()

    with pytest.raises(ValueError) as excinfo:
        p.set_default_command(func)
    msg = "func: cannot add arg x/--y: invalid option string"
    assert msg in str(excinfo.value)


def test_annotation():
    "Extracting argument help from function annotations (Python 3 only)."
    if not argh.six.PY3:
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


#------------------------------------------------------------------------------
#
# INTEGRATION TESTS
#

@pytest.mark.xfail(reason='TODO')
def test_guessing_integration():
    "guessing is used in dispatching"
    pass


def test_set_default_command_integration():
    @argh.arg('--foo', default=1)
    def cmd(args):
        return args.foo

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == '1\n'
    assert run(p, '--foo 2') == '2\n'
    assert run(p, '--help', exit=True)
