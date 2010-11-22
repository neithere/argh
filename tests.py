# -*- coding: utf-8 -*-

import sys
import unittest2 as unittest
import argparse
import argh
from argh import ArghParser, arg, add_commands, dispatch, plain_signature


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
    return u'you said {0}'.format(args.text) * repeat

@arg('text')
@plain_signature
def plain_echo(text):
    return u'you said {0}'.format(text)

@arg('--name', default='world')
def hello(args):
    return u'Hello {0}!'.format(args.name or 'world')

@arg('buddy')
def howdy(args):
    return u'Howdy {0}?'.format(args.buddy)

@arg('foo')
@arg('bar')
def foo_bar(args):
    return args.foo, args.bar


class ArghTestCase(unittest.TestCase):
    def setUp(self):
        #self.parser = build_parser(echo, plain_echo, foo=[hello, howdy])
        self.parser = DebugArghParser('PROG')
        self.parser.add_commands([echo, plain_echo, foo_bar])
        self.parser.add_commands([hello, howdy], namespace='greet')

    def _call_cmd(self, command_string):
        args = command_string.split() if command_string else command_string
        return self.parser.dispatch(args, intercept=True)

    def assert_cmd_returns(self, command_string, expected_result):
        """Executes given command using given parser and asserts that it prints
        given value.
        """
        try:
            result = self._call_cmd(command_string)
        except SystemExit:
            self.fail('Argument parsing failed for {0}'.format(command_string))
        self.assertEqual(result, expected_result)

    def assert_cmd_exits(self, command_string, message_regex=None):
        "When a command forces exit, it *may* fail, but may just print help."
        message_regex = str(message_regex)  # make sure None -> "None"
        with self.assertRaisesRegexp(SystemExit, message_regex):
            self.parser.dispatch(command_string.split())

    def assert_cmd_fails(self, command_string, message_regex):
        "exists with a message = fails"
        self.assert_cmd_exits(command_string, message_regex)

    def assert_cmd_doesnt_fail(self, command_string):
        """(for cases when a commands doesn't fail but also (maybe) doesn't
        return results and just prints them.)
        """
        result = self.assert_cmd_exits(command_string)

    def test_argv(self):
        _argv = sys.argv
        sys.argv = sys.argv[:1] + ['echo', 'hi there']
        self.assert_cmd_returns(None, 'you said hi there')
        sys.argv = _argv

    def test_invalid_choice(self):
        self.assert_cmd_fails('whatchamacallit', '^invalid choice')

    def test_echo(self):
        "A simple command is resolved to a function."
        self.assert_cmd_returns('echo foo', 'you said foo')

    def test_bool_action(self):
        "Action `store_true`/`store_false` is inferred from default value."
        self.assert_cmd_returns('echo --twice foo', 'you said fooyou said foo')

    def test_plain_signature(self):
        "Arguments can be passed to the function without a Namespace instance."
        self.assert_cmd_returns('plain-echo bar', 'you said bar')

    def test_bare_namespace(self):
        "A command can be resolved to a function, not a namespace."
        self.assert_cmd_fails('greet', 'too few arguments')
        self.assert_cmd_fails('greet --name=world', 'too few arguments')

    def test_namespaced_function(self):
        "A subcommand is resolved to a function."
        self.assert_cmd_returns('greet hello', u'Hello world!')
        self.assert_cmd_returns('greet hello --name=John', u'Hello John!')
        self.assert_cmd_fails('greet hello John', 'unrecognized arguments')
        self.assert_cmd_fails('greet howdy --name=John', 'too few arguments')
        self.assert_cmd_returns('greet howdy John', u'Howdy John?')

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
        self.assert_cmd_returns('foo-bar foo bar', 'foo\nbar')

class ConfirmTestCase(unittest.TestCase):
    def assert_choice(self, choice, expected, **kwargs):
        argh.raw_input = lambda prompt: choice
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
        argh.raw_input = raw_input_mock

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
            assert isinstance(prompt, str)
        argh.raw_input = raw_input_mock
        argh.confirm(u'привет')
