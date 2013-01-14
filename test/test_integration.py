# -*- coding: utf-8 -*-
"""
Integration Tests
~~~~~~~~~~~~~~~~~
"""
import sys
import re
import argparse

import mock
import pytest

import argh

from .base import DebugArghParser, run


@pytest.mark.xfail(reason='TODO')
def test_guessing_integration():
    "guessing is used in dispatching"
    assert 0


def test_set_default_command_integration():
    @argh.arg('--foo', default=1)
    def cmd(args):
        return args.foo

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == '1\n'
    assert run(p, '--foo 2') == '2\n'
    assert None == run(p, '--help', exit=True)


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


def test_all_specs_in_one():

    @argh.arg('foo')
    @argh.arg('--bar')
    @argh.arg('fox')
    @argh.arg('--baz')
    def cmd(foo, bar=1, *args, **kwargs):
        yield 'foo: {0}'.format(foo)
        yield 'bar: {0}'.format(bar)
        yield '*args: {0}'.format(args)
        for k in sorted(kwargs):
            yield '** {0}: {1}'.format(k, kwargs[k])

    p = DebugArghParser()
    p.set_default_command(cmd)

    # 1) bar=1 is treated as --bar so positionals from @arg that go **kwargs
    #    will still have higher priority than bar.
    # 2) *args, a positional with nargs='*', sits between two required
    #    positionals (foo and fox), so it gets nothing.
    assert run(p, 'one two') == (
        'foo: one\n'
        'bar: 1\n'
        '*args: ()\n'
        '** baz: None\n'
        '** fox: two\n')

    # two required positionals (foo and fox) get an argument each and one extra
    # is left; therefore the middle one is given to *args.
    assert run(p, 'one two three') == (
        'foo: one\n'
        'bar: 1\n'
        "*args: ('two',)\n"
        '** baz: None\n'
        '** fox: three\n')

    # two required positionals (foo and fox) get an argument each and two extra
    # are left; both are given to *args (it's greedy).
    assert run(p, 'one two three four') == (
        'foo: one\n'
        'bar: 1\n'
        "*args: ('two', 'three')\n"
        '** baz: None\n'
        '** fox: four\n')


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
        def parrot(dead=False):
            if dead:
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

    def test_processor(self):
        parrot = self._get_parrot()
        wrapped_parrot = argh.wrap_errors(ValueError)(parrot)

        def failure(err):
            return 'ERR: ' + str(err) + '!'
        processed_parrot = argh.wrap_errors(processor=failure)(wrapped_parrot)

        p = argh.ArghParser()
        p.set_default_command(processed_parrot)

        assert run(p, '--dead') == 'ERR: this parrot is no more!\n'


def test_argv():

    @argh.arg('text')
    def echo(args):
        return 'you said {0}'.format(args.text)

    p = DebugArghParser()
    p.add_commands([echo])

    _argv = sys.argv

    sys.argv = sys.argv[:1] + ['echo', 'hi there']
    assert run(p, None) == 'you said hi there\n'

    sys.argv = _argv


def test_commands_not_defined():
    p = DebugArghParser()

    assert run(p, '', {'raw_output': True}) == p.format_usage()
    assert run(p, '') == p.format_usage() + '\n'

    assert 'unrecognized arguments' in run(p, 'foo', exit=True)
    assert 'unrecognized arguments' in run(p, '--foo', exit=True)


def test_command_not_chosen():
    def cmd(args):
        return 1

    p = DebugArghParser()
    p.add_commands([cmd])

    if sys.version_info < (3,3):
        # Python before 3.3 exits with an error
        assert 'too few arguments' in run(p, '', exit=True)
    else:
        # Python since 3.3 returns a help message and doesn't exit
        assert 'usage:' in run(p, '')


def test_invalid_choice():
    def cmd(args):
        return 1

    # root level command

    p = DebugArghParser()
    p.add_commands([cmd])

    assert run(p, 'bar', exit=True).startswith('invalid choice')

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        assert 'too few arguments' in run(p, '--bar', exit=True)
    else:
        # Python since 3.3 exits with a more informative error
        assert run(p, '--bar', exit=True) == 'unrecognized arguments: --bar'

    # nested command

    p = DebugArghParser()
    p.add_commands([cmd], namespace='nest')

    assert run(p, 'nest bar', exit=True).startswith('invalid choice')

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        assert 'too few arguments' in run(p, 'nest --bar', exit=True)
    else:
        # Python since 3.3 exits with a more informative error
        assert run(p, 'nest --bar', exit=True) == 'unrecognized arguments: --bar'


def test_unrecognized_arguments():
    def cmd(args):
        return 1

    # single-command parser

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '--bar', exit=True) == 'unrecognized arguments: --bar'
    assert run(p, 'bar', exit=True) == 'unrecognized arguments: bar'

    # multi-command parser

    p = DebugArghParser()
    p.add_commands([cmd])

    assert run(p, 'cmd --bar', exit=True) == 'unrecognized arguments: --bar'
    assert run(p, 'cmd bar', exit=True) == 'unrecognized arguments: bar'


def test_echo():
    "A simple command is resolved to a function."

    @argh.arg('text')
    def echo(args):
        return 'you said {0}'.format(args.text)

    p = DebugArghParser()
    p.add_commands([echo])

    assert run(p, 'echo foo') == 'you said foo\n'


def test_bool_action():
    "Action `store_true`/`store_false` is inferred from default value."

    @argh.arg('--dead', default=False)
    def parrot(args):
        return 'this parrot is no more' if args.dead else 'beautiful plumage'

    p = DebugArghParser()
    p.add_commands([parrot])

    assert run(p, 'parrot') == 'beautiful plumage\n'
    assert run(p, 'parrot --dead') == 'this parrot is no more\n'


def test_bare_namespace():
    "A command can be resolved to a function, not a namespace."

    def hello():
        return 'hello world'

    p = DebugArghParser()
    p.add_commands([hello], namespace='greet')

    # without arguments

    if sys.version_info < (3,3):
        # Python before 3.3 exits with an error
        assert run(p, 'greet', exit=True) == 'too few arguments'
    else:
        # Python since 3.3 returns a help message and doesn't exit
        assert 'usage:' in run(p, 'greet', exit=True)

    # with an argument

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        message = 'too few arguments'
    else:
        # Python since 3.3 exits with a more informative error
        message = 'unrecognized arguments: --name=world'
    assert run(p, 'greet --name=world', exit=True) == message


def test_namespaced_function():
    "A subcommand is resolved to a function."

    def hello(name='world'):
        return 'Hello {0}!'.format(name or 'world')

    def howdy(buddy):
        return 'Howdy {0}?'.format(buddy)

    p = DebugArghParser()
    p.add_commands([hello, howdy], namespace='greet')

    assert run(p, 'greet hello') == 'Hello world!\n'
    assert run(p, 'greet hello --name=John') == 'Hello John!\n'
    assert run(p, 'greet hello John', exit=True) == 'unrecognized arguments: John'

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        message = 'too few arguments'
    else:
        # Python since 3.3 exits with a more informative error
        message = 'the following arguments are required: buddy'

    assert message in run(p, 'greet howdy --name=John', exit=True)
    assert run(p, 'greet howdy John') == 'Howdy John?\n'


def test_explicit_cmd_name():

    @argh.named('new-name')
    def orig_name():
        return 'ok'

    p = DebugArghParser()
    p.add_commands([orig_name])
    assert run(p, 'orig-name', exit=True).startswith('invalid choice')
    assert run(p, 'new-name') == 'ok\n'


def test_aliases():

    @argh.aliases('alias2', 'alias3')
    def alias1():
        return 'ok'

    p = DebugArghParser()
    p.add_commands([alias1])

    if argh.assembling.SUPPORTS_ALIASES:
        assert run(p, 'alias1') == 'ok\n'
        assert run(p, 'alias2') == 'ok\n'
        assert run(p, 'alias3') == 'ok\n'


def test_help_alias():
    p = DebugArghParser()

    # assert the commands don't fail

    assert None == run(p, '--help', exit=True)
    assert None == run(p, 'greet --help', exit=True)
    assert None == run(p, 'greet hello --help', exit=True)

    assert None == run(p, 'help', exit=True)
    assert None == run(p, 'help greet', exit=True)
    assert None == run(p, 'help greet hello', exit=True)


def test_arg_order():
    """Positional arguments are resolved in the order in which the @arg
    decorators are defined.
    """
    @argh.arg('foo')
    @argh.arg('bar')
    def cmd(args):
        return args.foo, args.bar

    p = DebugArghParser()
    p.set_default_command(cmd)
    assert run(p, 'foo bar') == 'foo\nbar\n'


def test_raw_output():
    "If the raw_output flag is set, no extra whitespace is added"

    def cmd(foo, bar):
        return foo, bar

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, 'foo bar') == 'foo\nbar\n'
    assert run(p, 'foo bar', {'raw_output': True}) == 'foobar'


def test_output_file():

    def cmd():
        return 'Hello world!'

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == 'Hello world!\n'
    assert run(p, '', {'output_file': None}) == 'Hello world!\n'


def test_command_error():

    def whiner_plain():
        raise argh.CommandError('I feel depressed.')

    def whiner_iterable():
        yield 'Hello...'
        raise argh.CommandError('I feel depressed.')

    p = DebugArghParser()
    p.add_commands([whiner_plain, whiner_iterable])

    assert run(p, 'whiner-plain') == 'I feel depressed.\n'
    assert run(p, 'whiner-iterable') == 'Hello...\nI feel depressed.\n'


def test_custom_namespace():

    @argh.expects_obj
    def cmd(args):
        return args.custom_value

    p = DebugArghParser()
    p.set_default_command(cmd)
    namespace = argparse.Namespace()
    namespace.custom_value = 'foo'

    assert run(p, '', {'namespace': namespace}) == 'foo\n'


def test_normalized_keys():
    """ Underscores in function args are converted to dashes and back.
    """
    def cmd(a_b):
        return a_b

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, 'hello') == 'hello\n'


@mock.patch('argh.assembling.COMPLETION_ENABLED', True)
def test_custom_argument_completer():
    "Issue #33: Enable custom per-argument shell completion"

    @argh.arg('foo', completer='STUB')
    def func(foo):
        pass

    p = argh.ArghParser()
    p.set_default_command(func)

    assert p._actions[-1].completer == 'STUB'


def test_class_members():
    "Issue #34: class members as commands"

    class Controller:
        var = 123

        def instance_meth(self, value):
            return value, self.var

        @classmethod
        def class_meth(cls, value):
            return value, cls.var

        @staticmethod
        def static_meth(value):
            return value, 'w00t?'

        @staticmethod
        def static_meth2(value):
            return value, 'huh!'

    controller = Controller()

    p = DebugArghParser()
    p.add_commands([
        controller.instance_meth,
        controller.class_meth,
        controller.static_meth,
        Controller.static_meth2,
    ])

    assert run(p, 'instance-meth foo') == 'foo\n123\n'
    assert run(p, 'class-meth foo') == 'foo\n123\n'
    assert run(p, 'static-meth foo') == 'foo\nw00t?\n'
    assert run(p, 'static-meth2 foo') == 'foo\nhuh!\n'
