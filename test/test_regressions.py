# -*- coding: utf-8 -*-
"""
Regression tests
~~~~~~~~~~~~~~~~
"""
from .base import DebugArghParser, run

import argh


def test_regression_issue12():
    """Issue #12: @command was broken if there were more than one argument
    to begin with same character (i.e. short option names were inferred
    incorrectly).
    """

    def cmd(foo=1, fox=2):
        yield 'foo {0}, fox {1}'.format(foo, fox)

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') ==  'foo 1, fox 2\n'
    assert run(p, '--foo 3') == 'foo 3, fox 2\n'
    assert run(p, '--fox 3') == 'foo 1, fox 3\n'
    assert 'unrecognized' in run(p, '-f 3', exit=True)


def test_regression_issue12_help_flag():
    """Issue #12: if an argument starts with "h", e.g. "--host",
    ArgumentError is raised because "--help" is always added by argh
    without decorators.
    """
    def ddos(host='localhost'):
        return 'so be it, {0}!'.format(host)

    # no help → no conflict
    p = DebugArghParser('PROG', add_help=False)
    p.set_default_command(ddos)
    assert run(p, '-h 127.0.0.1') == 'so be it, 127.0.0.1!\n'

    # help added → conflict → short name ignored
    p = DebugArghParser('PROG', add_help=True)
    p.set_default_command(ddos)
    assert None == run(p, '-h 127.0.0.1', exit=True)


def test_regression_issue27():
    """Issue #27: store_true is not set for inferred bool argument.

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
    assert run(p, 'grenade') == ('Three shall be the number '
                                 'thou shalt count\n')
    assert run(p, 'grenade --count 5') == '5 is right out\n'

    # default → action (store_true)
    assert run(p, 'parrot') == 'beautiful plumage\n'
    assert run(p, 'parrot --dead') == 'this parrot is no more\n'


def test_regression_issue31():
    """ Issue #31: Argh fails with parameter action type 'count' if a default
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
    assert '0\n' == run(p, '')
    assert '1\n' == run(p, '-v')
    assert '2\n' == run(p, '-vv')
