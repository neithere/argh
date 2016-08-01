# coding: utf-8
"""
Regression tests
~~~~~~~~~~~~~~~~
"""
import pytest
import argh

from .base import DebugArghParser, run


def test_regression_issue12():
    """
    Issue #12: @command was broken if there were more than one argument
    to begin with same character (i.e. short option names were inferred
    incorrectly).
    """

    def cmd(foo=1, fox=2):
        yield 'foo {0}, fox {1}'.format(foo, fox)

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '').out ==  'foo 1, fox 2\n'
    assert run(p, '--foo 3').out == 'foo 3, fox 2\n'
    assert run(p, '--fox 3').out == 'foo 1, fox 3\n'
    assert 'unrecognized' in run(p, '-f 3', exit=True)


def test_regression_issue12_help_flag():
    """
    Issue #12: if an argument starts with "h", e.g. "--host",
    ArgumentError is raised because "--help" is always added by argh
    without decorators.
    """
    def ddos(host='localhost'):
        return 'so be it, {0}!'.format(host)

    # no help → no conflict
    p = DebugArghParser('PROG', add_help=False)
    p.set_default_command(ddos)
    assert run(p, '-h 127.0.0.1').out == 'so be it, 127.0.0.1!\n'

    # help added → conflict → short name ignored
    p = DebugArghParser('PROG', add_help=True)
    p.set_default_command(ddos)
    assert None == run(p, '-h 127.0.0.1', exit=True)


def test_regression_issue27():
    """
    Issue #27: store_true is not set for inferred bool argument.

    :Reason: when @command was refactored, it stopped using @arg, but it is
    it was there that guesses (choices→type, default→type and
    default→action) were made.
    """
    def parrot(dead=False):
        return 'this parrot is no more' if dead else 'beautiful plumage'

    def grenade(count=3):
        if count == 3:
            return 'Three shall be the number thou shalt count'
        else:
            return '{0!r} is right out'.format(count)

    p = DebugArghParser()
    p.add_commands([parrot, grenade])

    # default → type (int)
    assert run(p, 'grenade').out == ('Three shall be the number '
                                     'thou shalt count\n')
    assert run(p, 'grenade --count 5').out == '5 is right out\n'

    # default → action (store_true)
    assert run(p, 'parrot').out == 'beautiful plumage\n'
    assert run(p, 'parrot --dead').out == 'this parrot is no more\n'


def test_regression_issue31():
    """
    Issue #31: Argh fails with parameter action type 'count' if a default
    value is provided.

    :Reason: assembling._guess() would infer type from default value without
        regard to the action.  _CountAction does not accept argument "type".

    :Solution: restricted type inferring to actions "store" and "append".
    """

    @argh.arg('-v', '--verbose', dest='verbose', action='count', default=0)
    def cmd(**kwargs):
        yield kwargs.get('verbose', -1)

    p = DebugArghParser()
    p.set_default_command(cmd)
    assert '0\n' == run(p, '').out
    assert '1\n' == run(p, '-v').out
    assert '2\n' == run(p, '-vv').out


def test_regression_issue47():
    @argh.arg('--foo-bar', default="full")
    def func(foo_bar):
        return 'hello'

    p = DebugArghParser()
    with pytest.raises(argh.assembling.AssemblingError) as excinfo:
        p.set_default_command(func)
    msg = ('func: argument "foo_bar" declared as positional (in function '
           'signature) and optional (via decorator)')
    assert excinfo.exconly().endswith(msg)


def test_regression_issue76():
    """
    Issue #76: optional arguments defaulting to the empty string break --help.

    This is also tested in integration tests but in a different way.
    """
    def cmd(foo=''):
        pass

    p = DebugArghParser()
    p.set_default_command(cmd)
    run(p, '--help', exit=True)


def test_regression_issue104():
    """
    Issue #76: Bug in the way **kwargs is handled

    **kwargs handling was broken in the case that required (no default
    value) positional argument names contained underscores.
    """
    def cmd(foo_foo, bar_bar, baz_baz=5, bip_bip=9, **kwargs):
        return '\n'.join([str(foo_foo), str(bar_bar), str(baz_baz),
                          str(bip_bip), str(kwargs)])

    p = DebugArghParser()
    p.set_default_command(cmd)
    expected = "abc\ndef\n8\n9\n{}\n"
    assert run(p, 'abc def --baz-baz 8').out == expected
