# -*- coding: utf-8 -*-
"""
Misc. Tests
~~~~~~~~~~~
"""
import sys
import argparse

import argh

from .base import (DebugArghParser, assert_cmd_regex,
                   assert_cmd_fails, assert_cmd_doesnt_fail, run)


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
        assert_cmd_fails(p, 'greet', 'too few arguments')
    else:
        # Python since 3.3 returns a help message and doesn't exit
        assert_cmd_regex(p, 'greet', 'usage:')

    # with an argument

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        message = 'too few arguments'
    else:
        # Python since 3.3 exits with a more informative error
        message = 'unrecognized arguments: --name=world'
    assert_cmd_fails(p, 'greet --name=world', message)


def test_namespaced_function():
    "A subcommand is resolved to a function."
    @argh.arg('--name', default='world')
    def hello(args):
        return 'Hello {0}!'.format(args.name or 'world')

    @argh.arg('buddy')
    def howdy(args):
        return 'Howdy {0}?'.format(args.buddy)

    p = DebugArghParser()
    p.add_commands([hello, howdy], namespace='greet')

    assert run(p, 'greet hello') == 'Hello world!\n'
    assert run(p, 'greet hello --name=John') == 'Hello John!\n'
    assert_cmd_fails(p, 'greet hello John', 'unrecognized arguments')

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        missing_arg_regex = 'too few arguments'
    else:
        # Python since 3.3 exits with a more informative error
        missing_arg_regex = 'the following arguments are required: buddy'

    assert_cmd_fails(p, 'greet howdy --name=John', missing_arg_regex)
    assert run(p, 'greet howdy John') == 'Howdy John?\n'


def test_explicit_cmd_name():
    @argh.named('new-name')
    def orig_name(args):
        return 'ok'

    p = DebugArghParser()
    p.add_commands([orig_name])
    assert_cmd_fails(p, 'orig-name', 'invalid choice')
    assert run(p, 'new-name') == 'ok\n'


def test_aliases():
    @argh.aliases('alias2', 'alias3')
    def alias1(args):
        return 'ok'

    p = DebugArghParser()
    p.add_commands([alias1])

    if argh.assembling.SUPPORTS_ALIASES:
        assert run(p, 'alias1') == 'ok\n'
        assert run(p, 'alias2') == 'ok\n'
        assert run(p, 'alias3') == 'ok\n'


def test_help_alias():
    p = DebugArghParser()

    assert_cmd_doesnt_fail(p, '--help')
    assert_cmd_doesnt_fail(p, 'greet --help')
    assert_cmd_doesnt_fail(p, 'greet hello --help')

    assert_cmd_doesnt_fail(p, 'help')
    assert_cmd_doesnt_fail(p, 'help greet')
    assert_cmd_doesnt_fail(p, 'help greet hello')


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
    @argh.arg('foo')
    @argh.arg('bar')
    def cmd(args):
        return args.foo, args.bar

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, 'foo bar') == 'foo\nbar\n'
    assert run(p, 'foo bar', {'raw_output': True}) == 'foobar'


def test_output_file():
    def cmd(args):
        return 'Hello world!'

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == 'Hello world!\n'
    assert run(p, '', {'output_file': None}) == 'Hello world!\n'


def test_command_error():
    def whiner_plain(args):
        raise argh.CommandError('I feel depressed.')

    def whiner_iterable(args):
        yield 'Hello...'
        raise argh.CommandError('I feel depressed.')

    p = DebugArghParser()
    p.add_commands([whiner_plain, whiner_iterable])

    assert run(p, 'whiner-plain') == 'I feel depressed.\n'
    assert run(p, 'whiner-iterable') == 'Hello...\nI feel depressed.\n'


def test_custom_namespace():
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
