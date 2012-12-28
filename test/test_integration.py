# -*- coding: utf-8 -*-
"""
Integration Tests
~~~~~~~~~~~~~~~~~
"""
import sys
import re

import pytest

import argh

from .base import DebugArghParser, run


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


def test_set_default_command_integration_merging():
    @argh.arg('--foo', help='bar')
    def cmd(foo=1):
        return foo

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == '1\n'
    assert run(p, '--foo 2') == '2\n'
    assert 'bar' in p.format_help()


#
# Function can be added to parser as is
#


def test_simple_function_no_args():
    def cmd():
        yield 1

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == '1\n'


def test_simple_function_positional():
    def cmd(x):
        yield x

    p = DebugArghParser()
    p.set_default_command(cmd)

    if sys.version_info < (3,3):
        msg = 'too few arguments'
    else:
        msg = 'the following arguments are required: x'
    assert run(p, '', exit=True) == msg
    assert run(p, 'foo') == 'foo\n'


def test_simple_function_defaults():
    def cmd(x='foo'):
        yield x

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == 'foo\n'
    assert run(p, 'bar', exit=True) == 'unrecognized arguments: bar'
    assert run(p, '--x bar') == 'bar\n'


def test_simple_function_varargs():

    def func(*file_paths):
        # `paths` is the single positional argument with nargs='*'
        yield ', '.join(file_paths)

    p = DebugArghParser()
    p.set_default_command(func)

    assert run(p, '') == '\n'
    assert run(p, 'foo') == 'foo\n'
    assert run(p, 'foo bar') == 'foo, bar\n'


def test_simple_function_kwargs():

    @argh.arg('foo')
    @argh.arg('--bar')
    def cmd(**kwargs):
        # `kwargs` contain all arguments not fitting ArgSpec.args and .varargs.
        # if ArgSpec.keywords in None, all @arg()'s will have to fit ArgSpec.args
        for k in sorted(kwargs):
            yield '{0}: {1}'.format(k, kwargs[k])

    p = DebugArghParser()
    p.set_default_command(cmd)

    if sys.version_info < (3,3):
        msg = 'too few arguments'
    else:
        msg = 'the following arguments are required: foo'
    assert run(p, '', exit=True) == msg
    assert run(p, 'hello') == 'bar: None\nfoo: hello\n'
    assert run(p, '--bar 123', exit=True) == msg
    assert run(p, 'hello --bar 123') == 'bar: 123\nfoo: hello\n'


def test_simple_function_multiple():
    pass


def test_simple_function_nested():
    pass


def test_class_method_as_command():
    pass


def test_arg_merged():
    """ @arg merges into function signature.
    """
    @argh.arg('my', help='a moose once bit my sister')
    @argh.arg('-b', '--brain', help='i am made entirely of wood')
    def gumby(my, brain=None):
        return my, brain, 'hurts'

    p = DebugArghParser('PROG')
    p.set_default_command(gumby)
    help_msg = p.format_help()

    assert 'a moose once bit my sister' in help_msg
    assert 'i am made entirely of wood' in help_msg


def test_arg_mismatch_positional():
    """ @arg must match function signature if @command is applied.
    """
    @argh.arg('bogus-argument')
    def confuse_a_cat(vet, funny_things=123):
        return vet, funny_things

    p = DebugArghParser('PROG')
    with pytest.raises(ValueError) as excinfo:
        p.set_default_command(confuse_a_cat)

    msg = ("confuse_a_cat: argument bogus-argument does not fit "
           "function signature: vet, -f/--funny-things")
    assert msg in str(excinfo.value)


def test_arg_mismatch_flag():
    """ @arg must match function signature if @command is applied.
    """
    @argh.arg('--bogus-argument')
    def confuse_a_cat(vet, funny_things=123):
        return vet, funny_things

    p = DebugArghParser('PROG')
    with pytest.raises(ValueError) as excinfo:
        p.set_default_command(confuse_a_cat)

    msg = ("confuse_a_cat: argument --bogus-argument does not fit "
           "function signature: vet, -f/--funny-things")
    assert msg in str(excinfo.value)


def test_backwards_compatibility_issue29():
    @argh.arg('foo')
    @argh.arg('--bar', default=1)
    def old(args):
        yield '{0} {1}'.format(args.foo, args.bar)

    @argh.command
    def old_marked(foo, bar=1):
        yield '{0} {1}'.format(foo, bar)

    def new(foo, bar=1):
        yield '{0} {1}'.format(foo, bar)

    p = DebugArghParser('PROG')
    p.add_commands([old, old_marked, new])

    assert 'ok 1\n' == run(p, 'old ok')
    assert 'ok 5\n' == run(p, 'old ok --bar 5')

    assert 'ok 1\n' == run(p, 'old-marked ok')
    assert 'ok 5\n' == run(p, 'old-marked ok --bar 5')

    assert 'ok 1\n' == run(p, 'new ok')
    assert 'ok 5\n' == run(p, 'new ok --bar 5')


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
