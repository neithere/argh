# -*- coding: utf-8 -*-
"""
Argh Tests
~~~~~~~~~~
"""
import sys
import re
from argh.six import (
    PY3, BytesIO, StringIO, u, string_types, text_type, binary_type,
    iteritems
)
import pytest
import argparse
import argh
import argh.helpers
from argh import (
    aliases, ArghParser, arg, command, CommandError, dispatch_command,
    dispatch_commands, plain_signature, wrap_errors
)


def make_IO():
    "Returns a file object of the same type as `sys.stdout`."
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

@aliases('alias2', 'alias3')
def alias1(args):
    return 'ok'

@argh.named('new-name')
def orig_name(args):
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


class BaseArghTestCase(object):
    commands = {}

    def setup_method(self, method):
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

        if isinstance(expected_result, re._pattern_type):
            assert expected_result.match(result), \
                '/{0}/ !~ {1!r}'.format(expected_result.pattern, result)
        else:
            assert expected_result == result

    def assert_cmd_regex(self, command_string, pattern, **kwargs):
        return self.assert_cmd_returns(command_string, re.compile(pattern),
                                       **kwargs)

    def assert_cmd_exits(self, command_string, message_regex=''):
        "When a command forces exit, it *may* fail, but may just print help."
        with pytest.raises(SystemExit) as excinfo:
            self.parser.dispatch(command_string.split())
        assert re.match(message_regex, text_type(excinfo.value))

    def assert_cmd_fails(self, command_string, message_regex):
        "exists with a message = fails"
        self.assert_cmd_exits(command_string, message_regex)

    def assert_cmd_doesnt_fail(self, command_string):
        """(for cases when a commands doesn't fail but also (maybe) doesn't
        return results and just prints them.)
        """
        self.assert_cmd_exits(command_string)


class TestArgh(BaseArghTestCase):
    commands = {
        None: [echo, plain_echo, foo_bar, alias1, orig_name,
               whiner_plain, whiner_iterable, custom_namespace],
        'greet': [hello, howdy]
    }

    def test_argv(self):
        _argv = sys.argv
        sys.argv = sys.argv[:1] + ['echo', 'hi there']
        self.assert_cmd_returns(None, 'you said hi there\n')
        sys.argv = _argv

    def test_no_command(self):
        if sys.version_info < (3,3):
            # Python before 3.3 exits with an error
            self.assert_cmd_fails('', 'too few arguments')
        else:
            # Python since 3.3 returns a help message and doesn't exit
            self.assert_cmd_regex('', 'usage:')

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

        # without arguments

        if sys.version_info < (3,3):
            # Python before 3.3 exits with an error
            self.assert_cmd_fails('greet', 'too few arguments')
        else:
            # Python since 3.3 returns a help message and doesn't exit
            self.assert_cmd_regex('greet', 'usage:')

        # with an argument

        if sys.version_info < (3,3):
            # Python before 3.3 exits with a less informative error
            self.assert_cmd_fails('greet --name=world', 'too few arguments')
        else:
            # Python since 3.3 exits with a more informative error
            self.assert_cmd_fails('greet --name=world',
                                  'unrecognized arguments: --name=world')

    def test_namespaced_function(self):
        "A subcommand is resolved to a function."
        self.assert_cmd_returns('greet hello', 'Hello world!\n')
        self.assert_cmd_returns('greet hello --name=John', 'Hello John!\n')
        self.assert_cmd_fails('greet hello John', 'unrecognized arguments')

        if sys.version_info < (3,3):
            # Python before 3.3 exits with a less informative error
            missing_arg_regex = 'too few arguments'
        else:
            # Python since 3.3 exits with a more informative error
            missing_arg_regex = 'the following arguments are required: buddy'

        self.assert_cmd_fails('greet howdy --name=John', missing_arg_regex)
        self.assert_cmd_returns('greet howdy John', 'Howdy John?\n')

    def test_explicit_cmd_name(self):
        self.assert_cmd_fails('orig-name', 'invalid choice')
        self.assert_cmd_returns('new-name', 'ok\n')

    def test_aliases(self):
        if argh.assembling.SUPPORTS_ALIASES:
            self.assert_cmd_returns('alias1', 'ok\n')
            self.assert_cmd_returns('alias2', 'ok\n')
            self.assert_cmd_returns('alias3', 'ok\n')

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

    def test_normalized_keys(self):
        """ Underscores in function args are converted to dashes and back.
        """
        @command
        def cmd(a_b):
            return a_b

        self.parser = DebugArghParser()
        self.parser.set_default_command(cmd)
        self.assert_cmd_returns('hello', 'hello\n')


class TestCommandDecorator(BaseArghTestCase):
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

    def test_regression_issue12_help_flag(self):
        """Issue #12: if an argument starts with "h", e.g. "--host",
        ArgumentError is raised because "--help" is always added by argh
        without decorators.
        """
        @command
        def ddos(host='localhost'):
            return 'so be it, {0}!'.format(host)

        # no help → no conflict
        self.parser = DebugArghParser('PROG', add_help=False)
        self.parser.set_default_command(ddos)
        self.assert_cmd_returns('-h 127.0.0.1', 'so be it, 127.0.0.1!\n')

        # help added → conflict → short name ignored
        self.parser = DebugArghParser('PROG', add_help=True)
        self.parser.set_default_command(ddos)
        self.assert_cmd_fails('-h 127.0.0.1', '')

    def test_regression_issue27(self):
        """Issue #27: store_true is not set for inferred bool argument.

        Reason: when @command was refactored, it stopped using @arg, but it is
        it was there that guesses (choices→type, default→type and
        default→action) were made.
        """
        @command
        def parrot(dead=False):
            return 'this parrot is no more' if dead else 'beautiful plumage'

        @command
        def grenade(count=3):
            if count == 3:
                return 'Three shall be the number thou shalt count'
            else:
                return '{0!r} is right out'.format(count)

        self.parser = DebugArghParser()
        self.parser.add_commands([parrot, grenade])

        # default → type (int)
        self.assert_cmd_returns('grenade', 'Three shall be the number '
                                           'thou shalt count\n')
        self.assert_cmd_returns('grenade --count 5', '5 is right out\n')

        # default → action (store_true)
        self.assert_cmd_returns('parrot', 'beautiful plumage\n')
        self.assert_cmd_returns('parrot --dead', 'this parrot is no more\n')



    def test_declared_vs_inferred_merging(self):
        """ @arg merges into function signature if @command is applied.
        """
        @command
        @arg('my', help='a moose once bit my sister')
        @arg('-b', '--brain', help='i am made entirely of wood')
        def gumby(my, brain=None):
            return my, brain, 'hurts'

        self.parser = DebugArghParser('PROG')
        self.parser.set_default_command(gumby)

        help_msg = self.parser.format_help()
        assert 'a moose once bit my sister' in help_msg
        assert 'i am made entirely of wood' in help_msg

    def test_declared_vs_inferred_mismatch_positional(self):
        """ @arg must match function signature if @command is applied.
        """
        @command
        @arg('bogus-argument')
        def confuse_a_cat(vet, funny_things=123):
            return vet, funny_things

        self.parser = DebugArghParser('PROG')
        with pytest.raises(ValueError) as excinfo:
            self.parser.set_default_command(confuse_a_cat)
        msg = ("confuse_a_cat: argument bogus-argument does not fit "
               "function signature: -f/--funny-things, vet")
        assert msg in str(excinfo.value)

    def test_declared_vs_inferred_mismatch_flag(self):
        """ @arg must match function signature if @command is applied.
        """
        @command
        @arg('--bogus-argument')
        def confuse_a_cat(vet, funny_things=123):
            return vet, funny_things

        self.parser = DebugArghParser('PROG')
        with pytest.raises(ValueError) as excinfo:
            self.parser.set_default_command(confuse_a_cat)
        msg = ("confuse_a_cat: argument --bogus-argument does not fit "
               "function signature: -f/--funny-things, vet")
        assert msg in str(excinfo.value)


class TestErrorWrapping(BaseArghTestCase):
    commands = {None: [strict_hello, strict_hello_smart]}
    def test_error_raised(self):
        with pytest.raises(AssertionError) as excinfo:
            self.parser.dispatch(['strict-hello', 'John'])
        assert re.match('Do it yourself', text_type(excinfo.value))

    def test_error_wrapped(self):
        self.assert_cmd_returns('strict-hello-smart John', 'Do it yourself\n')
        self.assert_cmd_returns('strict-hello-smart world', 'Hello world\n')


class TestNoCommands(BaseArghTestCase):
    "Edge case: no commands defined"
    commands = {}
    def test_no_command(self):
        self.assert_cmd_returns('', self.parser.format_usage(), raw_output=True)
        self.assert_cmd_returns('', self.parser.format_usage()+'\n')


class TestDefaultCommand(BaseArghTestCase):
    def setup_method(self, method):
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
        with pytest.raises(RuntimeError) as excinfo:
            p.add_commands([two])
        assert re.match('Cannot add commands to a single-command parser',
                        text_type(excinfo.value))

    def test_prevent_conflict_with_subparsers(self):
        def one(args): return 1
        def two(args): return 2

        p = DebugArghParser('PROG')
        p.add_commands([one])
        with pytest.raises(RuntimeError) as excinfo:
            p.set_default_command(two)
        assert re.match('Cannot set default command to a parser with '
                        'existing subparsers',
                        text_type(excinfo.value))


class TestDispatchCommand(BaseArghTestCase):
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
        assert expected_result == result

    def test_dispatch_command_shortcut(self):

        @arg('--foo', default=1)
        def main(args):
            return args.foo

        self.assert_cmd_returns(main, '', '1\n')
        self.assert_cmd_returns(main, '--foo 2', '2\n')


class TestDispatchCommands(BaseArghTestCase):
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
        assert expected_result == result

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


class TestConfirm(object):
    def assert_choice(self, choice, expected, **kwargs):
        argh.io._input = lambda prompt: choice
        assert argh.confirm('test', **kwargs) == expected

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
        argh.io._input = raw_input_mock

        argh.confirm('do smth')
        assert prompts[-1] == 'do smth? (y/n)'

        argh.confirm('do smth', default=None)
        assert prompts[-1] == 'do smth? (y/n)'

        argh.confirm('do smth', default=True)
        assert prompts[-1] == 'do smth? (Y/n)'

        argh.confirm('do smth', default=False)
        assert prompts[-1] == 'do smth? (y/N)'

    def test_encoding(self):
        "Unicode and bytes are accepted as prompt message"
        def raw_input_mock(prompt):
            if not PY3:
                assert isinstance(prompt, binary_type)
        argh.io._input = raw_input_mock
        argh.confirm(u('привет'))


class TestAnnotations(BaseArghTestCase):
    """ Tests for extracting argument documentation from function annotations
    (Python 3 only).
    """
    def test_annotation(self):
        if PY3:
            # Yes, this looks horrible, but otherwise Python 2 would die
            # screaming and cursing as it is completely in the dark about the
            # sweetness of annotations and we can but tolerate its ignorance.
            ns = {}
            exec("def cmd(foo : 'quux' = 123):\n    'bar'\npass", None, ns)
            cmd = ns['cmd']
            p = ArghParser()
            p.set_default_command(command(cmd))
            prog_help = p.format_help()
            assert 'quux' in prog_help


class TestAssembling(BaseArghTestCase):
    def test_command_decorator(self):
        """The @command decorator creates arguments from function signature.
        """
        @arg('x', '--y')
        def cmd(args):
            return

        with pytest.raises(ValueError) as excinfo:
            self.parser.set_default_command(cmd)
        msg = "cmd: cannot add arg x/--y: invalid option string"
        assert msg in str(excinfo.value)
