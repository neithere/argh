# -*- coding: utf-8 -*-
"""
Decorator Tests
~~~~~~~~~~~~~~~
"""
import re

import pytest

import argh

from base import DebugArghParser, run


def test_command_decorator():
    """The @command decorator creates arguments from function signature.
    """
    @argh.command
    def cmd(text='Hello'):
        yield text

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == 'Hello\n'
    assert run(p, '--text=hi') == 'hi\n'


def test_declared_vs_inferred_merging():
    """ @arg merges into function signature if @command is applied.
    """
    @argh.command
    @argh.arg('my', help='a moose once bit my sister')
    @argh.arg('-b', '--brain', help='i am made entirely of wood')
    def gumby(my, brain=None):
        return my, brain, 'hurts'

    p = DebugArghParser('PROG')
    p.set_default_command(gumby)
    help_msg = p.format_help()

    assert 'a moose once bit my sister' in help_msg
    assert 'i am made entirely of wood' in help_msg


def test_declared_vs_inferred_mismatch_positional():
    """ @arg must match function signature if @command is applied.
    """
    @argh.command
    @argh.arg('bogus-argument')
    def confuse_a_cat(vet, funny_things=123):
        return vet, funny_things

    p = DebugArghParser('PROG')
    with pytest.raises(ValueError) as excinfo:
        p.set_default_command(confuse_a_cat)

    msg = ("confuse_a_cat: argument bogus-argument does not fit "
           "function signature: -f/--funny-things, vet")
    assert msg in str(excinfo.value)


def test_declared_vs_inferred_mismatch_flag():
    """ @arg must match function signature if @command is applied.
    """
    @argh.command
    @argh.arg('--bogus-argument')
    def confuse_a_cat(vet, funny_things=123):
        return vet, funny_things

    p = DebugArghParser('PROG')
    with pytest.raises(ValueError) as excinfo:
        p.set_default_command(confuse_a_cat)

    msg = ("confuse_a_cat: argument --bogus-argument does not fit "
           "function signature: -f/--funny-things, vet")
    assert msg in str(excinfo.value)


class TestErrorWrapping:

    def _get_parrot(self):
        @argh.arg('--dead', default=False)
        def parrot(args):
            if args.dead:
                raise ValueError('this parrot is no more')
            else:
                return 'beautiful plumage'

        return parrot

    def test_error_raised(self):
        parrot = self._get_parrot()

        p = DebugArghParser()
        p.set_default_command(parrot)

        assert run(p, '') == 'beautiful plumage\n'
        with pytest.raises(ValueError) as excinfo:
            run(p, '--dead')
        assert re.match('this parrot is no more', str(excinfo.value))

    def test_error_wrapped(self):
        parrot = self._get_parrot()
        wrapped_parrot = argh.wrap_errors(ValueError)(parrot)

        p = DebugArghParser()
        p.set_default_command(wrapped_parrot)

        assert run(p, '') == 'beautiful plumage\n'
        assert run(p, '--dead') == 'this parrot is no more\n'
