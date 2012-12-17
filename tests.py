# -*- coding: utf-8 -*-

import sys
from argh.six import (
    PY3, BytesIO, StringIO, u, string_types, text_type, binary_type,
    iteritems
)
import unittest2 as unittest
import argparse
import argh.helpers
from argh import (
    alias, ArghParser, arg, command, CommandError, dispatch_command,
    dispatch_commands, plain_signature, wrap_errors
)
from argh import completion


def make_IO():
    # NOTE: this is according to sys.stdout
    if PY3:
        return StringIO()
    else:
        return BytesIO()

class DebugArghParser(ArghParser):
    "(does not print stuff to stderr on exit)"

    def exit(self, status=0, message=None):
        raise SystemExit(message)

    def error(self, message):
        self.exit(2, message)


@arg('text')
@arg('--twice', default=False, help='repeat twice')
def echo(args):
    repeat = 2 if args.twice else 1
    return (u('you said {0}').format(args.text)) * repeat

@arg('text')
@plain_signature
def plain_echo(text):
    return u('you said {0}').format(text)

@arg('--name', default='world')
def hello(args):
    return u('Hello {0}!').format(args.name or 'world')

@arg('buddy')
def howdy(args):
    return u('Howdy {0}?').format(args.buddy)

@alias('aliased')
def do_aliased(args):
    return 'ok'

@arg('foo')
@arg('bar')
def foo_bar(args):
    return args.foo, args.bar

def custom_namespace(args):
    return args.custom_value

def whiner_plain(args):
    raise CommandError('I feel depressed.')

def whiner_iterable(args):
    yield 'Hello...'
    raise CommandError('I feel depressed.')

@arg('text')
def strict_hello(args):
    assert args.text == 'world', 'Do it yourself'  # bad manners :-(
    yield 'Hello {0}'.format(args.text)

@arg('text')
@wrap_errors(AssertionError)
def strict_hello_smart(args):
    assert args.text == 'world', 'Do it yourself'  # bad manners :-(
    yield 'Hello {0}'.format(args.text)

@command
def command_deco(text='Hello'):
    yield text

@command
def command_deco_issue12(foo=1, fox=2):
    yield u('foo {0}, fox {1}').format(foo, fox)


class BaseArghTestCase(unittest.TestCase):
    commands = {}

    def setUp(self):
        self.parser = DebugArghParser('PROG')
        for namespace, commands in iteritems(self.commands):
            self.parser.add_commands(commands, namespace=namespace)

    def _call_cmd(self, command_string, **kwargs):
        if isinstance(command_string, string_types):
            args = command_string.split()
        else:
            args = command_string

        io = make_IO()

        if 'output_file' not in kwargs:
            kwargs['output_file'] = io

        result = self.parser.dispatch(args, **kwargs)

        if kwargs.get('output_file') is None:
            return result
        else:
            io.seek(0)
            return io.read()

    def assert_cmd_returns(self, command_string, expected_result, **kwargs):
        """Executes given command using given parser and asserts that it prints
        given value.
        """
        try:
            result = self._call_cmd(command_string, **kwargs)
        except SystemExit as error:
            self.fail('Argument parsing failed for {0!r}: {1!r}'.format(
                command_string, error))
        self.assertEqual(result, expected_result)

    def assert_cmd_exits(self, command_string, message_regex=None):
        "When a command forces exit, it *may* fail, but may just print help."
        message_regex = text_type(message_regex)  # make sure None -> "None"
        f = lambda: self.parser.dispatch(command_string.split())
        self.assertRaisesRegexp(SystemExit, message_regex, f)

    def assert_cmd_fails(self, command_string, message_regex):
        "exists with a message = fails"
        self.assert_cmd_exits(command_string, message_regex)

    def assert_cmd_doesnt_fail(self, command_string):
        """(for cases when a commands doesn't fail but also (maybe) doesn't
        return results and just prints them.)
        """
        self.assert_cmd_exits(command_string)


class ArghTestCase(BaseArghTestCase):
    commands = {
        None: [echo, plain_echo, foo_bar, do_aliased,
               whiner_plain, whiner_iterable, custom_namespace],
        'greet': [hello, howdy]
    }

    def test_argv(self):
        _argv = sys.argv
        sys.argv = sys.argv[:1] + ['echo', 'hi there']
        self.assert_cmd_returns(None, 'you said hi there\n')
        sys.argv = _argv

    def test_no_command(self):
        self.assert_cmd_fails('', 'too few arguments')

    def test_invalid_choice(self):
        self.assert_cmd_fails('whatchamacallit', '^invalid choice')

    def test_echo(self):
        "A simple command is resolved to a function."
        self.assert_cmd_returns('echo foo', 'you said foo\n')

    def test_bool_action(self):
        "Action `store_true`/`store_false` is inferred from default value."
        self.assert_cmd_returns('echo --twice foo', 'you said fooyou said foo\n')

    def test_plain_signature(self):
        "Arguments can be passed to the function without a Namespace instance."
        self.assert_cmd_returns('plain-echo bar', 'you said bar\n')

    def test_bare_namespace(self):
        "A command can be resolved to a function, not a namespace."
        self.assert_cmd_fails('greet', 'too few arguments')
        self.assert_cmd_fails('greet --name=world', 'too few arguments')

    def test_namespaced_function(self):
        "A subcommand is resolved to a function."
        self.assert_cmd_returns('greet hello', 'Hello world!\n')
        self.assert_cmd_returns('greet hello --name=John', 'Hello John!\n')
        self.assert_cmd_fails('greet hello John', 'unrecognized arguments')
        self.assert_cmd_fails('greet howdy --name=John', 'too few arguments')
        self.assert_cmd_returns('greet howdy John', 'Howdy John?\n')

    def test_alias(self):
        self.assert_cmd_returns('aliased', 'ok\n')

    def test_help_alias(self):
        self.assert_cmd_doesnt_fail('--help')
        self.assert_cmd_doesnt_fail('greet --help')
        self.assert_cmd_doesnt_fail('greet hello --help')

        self.assert_cmd_doesnt_fail('help')
        self.assert_cmd_doesnt_fail('help greet')
        self.assert_cmd_doesnt_fail('help greet hello')

    def test_arg_order(self):
        """Positional arguments are resolved in the order in which the @arg
        decorators are defined.
        """
        self.assert_cmd_returns('foo-bar foo bar', 'foo\nbar\n')

    def test_raw_output(self):
        "If the raw_output flag is set, no extra whitespace is added"
        self.assert_cmd_returns('foo-bar foo bar', 'foo\nbar\n')
        self.assert_cmd_returns('foo-bar foo bar', 'foobar', raw_output=True)

    def test_output_file(self):
        self.assert_cmd_returns('greet hello', 'Hello world!\n')
        self.assert_cmd_returns('greet hello', 'Hello world!\n', output_file=None)

    def test_command_error(self):
        self.assert_cmd_returns('whiner-plain', 'I feel depressed.\n')
        self.assert_cmd_returns('whiner-iterable', 'Hello...\nI feel depressed.\n')

    def test_custom_namespace(self):
        namespace = argparse.Namespace()
        namespace.custom_value = 'foo'
        self.assert_cmd_returns('custom-namespace', 'foo\n',
                                namespace=namespace)


class CommandDecoratorTests(BaseArghTestCase):
    commands = {None: [command_deco, command_deco_issue12]}

    def test_command_decorator(self):
        """The @command decorator creates arguments from function signature.
        """
        self.assert_cmd_returns('command-deco', 'Hello\n')
        self.assert_cmd_returns('command-deco --text=hi', 'hi\n')

    def test_regression_issue12(self):
        """Issue #12: @command was broken if there were more than one argument
        to begin with same character (i.e. short option names were inferred
        incorrectly).
        """
        self.assert_cmd_returns('command-deco-issue12', 'foo 1, fox 2\n')
        self.assert_cmd_returns('command-deco-issue12 --foo 3', 'foo 3, fox 2\n')
        self.assert_cmd_returns('command-deco-issue12 --fox 3', 'foo 1, fox 3\n')
        self.assert_cmd_fails('command-deco-issue12 -f 3', 'unrecognized')


class ErrorWrappingTestCase(BaseArghTestCase):
    commands = {None: [strict_hello, strict_hello_smart]}
    def test_error_raised(self):
        f = lambda: self.parser.dispatch(['strict-hello', 'John'])
        self.assertRaisesRegexp(AssertionError, 'Do it yourself', f)

    def test_error_wrapped(self):
        self.assert_cmd_returns('strict-hello-smart John', 'Do it yourself\n')
        self.assert_cmd_returns('strict-hello-smart world', 'Hello world\n')


class NoCommandsTestCase(BaseArghTestCase):
    "Edge case: no commands defined"
    commands = {}
    def test_no_command(self):
        self.assert_cmd_returns('', self.parser.format_usage(), raw_output=True)
        self.assert_cmd_returns('', self.parser.format_usage()+'\n')


class DefaultCommandTestCase(BaseArghTestCase):
    def setUp(self):
        self.parser = DebugArghParser('PROG')

        @arg('--foo', default=1)
        def main(args):
            return args.foo

        self.parser.set_default_command(main)

    def test_default_command(self):
        self.assert_cmd_returns('', '1\n')
        self.assert_cmd_returns('--foo 2', '2\n')
        self.assert_cmd_exits('--help')

    def test_prevent_conflict_with_single_command(self):
        def one(args): return 1
        def two(args): return 2

        p = DebugArghParser('PROG')
        p.set_default_command(one)
        with self.assertRaisesRegexp(RuntimeError,
                               'Cannot add commands to a single-command parser'):
            p.add_commands([two])

    def test_prevent_conflict_with_subparsers(self):
        def one(args): return 1
        def two(args): return 2

        p = DebugArghParser('PROG')
        p.add_commands([one])
        with self.assertRaisesRegexp(RuntimeError,
                               'Cannot set default command to a parser with '
                               'existing subparsers'):
            p.set_default_command(two)


class DispatchCommandTestCase(BaseArghTestCase):
    "Tests for :func:`argh.helpers.dispatch_command`"

    def _dispatch_and_capture(self, func, command_string, **kwargs):
        if isinstance(command_string, string_types):
            args = command_string.split()
        else:
            args = command_string

        io = make_IO()
        if 'output_file' not in kwargs:
            kwargs['output_file'] = io

        result = dispatch_command(func, args, **kwargs)

        if kwargs.get('output_file') is None:
            return result
        else:
            io.seek(0)
            return io.read()

    def assert_cmd_returns(self, func, command_string, expected_result, **kwargs):
        """Executes given command using given parser and asserts that it prints
        given value.
        """
        try:
            result = self._dispatch_and_capture(func, command_string, **kwargs)
        except SystemExit as error:
            self.fail('Argument parsing failed for {0!r}: {1!r}'.format(
                command_string, error))
        self.assertEqual(result, expected_result)

    def test_dispatch_command_shortcut(self):

        @arg('--foo', default=1)
        def main(args):
            return args.foo

        self.assert_cmd_returns(main, '', '1\n')
        self.assert_cmd_returns(main, '--foo 2', '2\n')


class DispatchCommandsTestCase(BaseArghTestCase):
    "Tests for :func:`argh.helpers.dispatch_commands`"

    def _dispatch_and_capture(self, funcs, command_string, **kwargs):
        if isinstance(command_string, string_types):
            args = command_string.split()
        else:
            args = command_string

        io = make_IO()
        if 'output_file' not in kwargs:
            kwargs['output_file'] = io

        result = dispatch_commands(funcs, args, **kwargs)

        if kwargs.get('output_file') is None:
            return result
        else:
            io.seek(0)
            return io.read()

    def assert_cmd_returns(self, funcs, command_string, expected_result, **kwargs):
        """Executes given command using given parser and asserts that it prints
        given value.
        """
        try:
            result = self._dispatch_and_capture(funcs, command_string, **kwargs)
        except SystemExit as error:
            self.fail('Argument parsing failed for {0!r}: {1!r}'.format(
                command_string, error))
        self.assertEqual(result, expected_result)

    def test_dispatch_commands_shortcut(self):

        @arg('-x', default=1)
        def foo(args):
            return args.x

        @arg('-y', default=2)
        def bar(args):
            return args.y

        self.assert_cmd_returns([foo, bar], 'foo', '1\n')
        self.assert_cmd_returns([foo, bar], 'foo -x 5', '5\n')
        self.assert_cmd_returns([foo, bar], 'bar', '2\n')


class ConfirmTestCase(unittest.TestCase):
    def assert_choice(self, choice, expected, **kwargs):
        argh.helpers.raw_input = lambda prompt: choice
        self.assertEqual(argh.confirm('test', **kwargs), expected)

    def test_simple(self):
        self.assert_choice('', None)
        self.assert_choice('', None, default=None)
        self.assert_choice('', True, default=True)
        self.assert_choice('', False, default=False)

        self.assert_choice('y', True)
        self.assert_choice('y', True, default=True)
        self.assert_choice('y', True, default=False)
        self.assert_choice('y', True, default=None)

        self.assert_choice('n', False)
        self.assert_choice('n', False, default=True)
        self.assert_choice('n', False, default=False)
        self.assert_choice('n', False, default=None)

        self.assert_choice('x', None)

    def test_prompt(self):
        "Prompt is properly formatted"
        prompts = []

        def raw_input_mock(prompt):
            prompts.append(prompt)
        argh.helpers.raw_input = raw_input_mock

        argh.confirm('do smth')
        self.assertEqual(prompts[-1], 'do smth? (y/n)')

        argh.confirm('do smth', default=None)
        self.assertEqual(prompts[-1], 'do smth? (y/n)')

        argh.confirm('do smth', default=True)
        self.assertEqual(prompts[-1], 'do smth? (Y/n)')

        argh.confirm('do smth', default=False)
        self.assertEqual(prompts[-1], 'do smth? (y/N)')

    def test_encoding(self):
        "Unicode and bytes are accepted as prompt message"
        def raw_input_mock(prompt):
            if not PY3:
                assert isinstance(prompt, binary_type)
        argh.helpers.raw_input = raw_input_mock
        argh.confirm(u('привет'))


class CompletionTestCase(unittest.TestCase):
    def setUp(self):
        "Declare some commands and allocate two namespaces for them"
        def echo(args):
            return args

        def load(args):
            return 'fake load'

        @arg('--format')
        def dump(args):
            return 'fake dump'

        self.parser = DebugArghParser()
        self.parser.add_commands([echo], namespace='silly')
        self.parser.add_commands([load, dump], namespace='fixtures')

    def assert_choices(self, arg_string, expected):
        args = arg_string.split()
        cwords = args
        cword = len(args) + 1
        choices = completion._autocomplete(self.parser, cwords, cword)
        self.assertEqual(' '.join(sorted(choices)), expected)

    def test_root(self):
        self.assert_choices('', 'fixtures silly')

    def test_root_missing(self):
        self.assert_choices('xyz', '')

    def test_root_partial(self):
        self.assert_choices('f', 'fixtures')
        self.assert_choices('fi', 'fixtures')
        self.assert_choices('s', 'silly')

    def test_inner(self):
        self.assert_choices('fixtures', 'dump load')
        self.assert_choices('silly', 'echo')

    def test_inner_partial(self):
        self.assert_choices('fixtures d', 'dump')
        self.assert_choices('fixtures dum', 'dump')
        self.assert_choices('silly e', 'echo')

    def test_inner_extra(self):
        self.assert_choices('silly echo foo', '')

    @unittest.expectedFailure
    def test_inner_options(self):
        self.assert_choices('fixtures dump', '--format')
        self.assert_choices('silly echo', 'text')
