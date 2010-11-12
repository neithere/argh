# -*- coding: utf-8 -*-

import sys
import unittest2 as unittest
import argparse
from argh import ArghParser, arg, add_commands, dispatch, plain_signature


@arg('text')
def echo(args):
    return u'you said {0}'.format(args.text)

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


class ArghTestCase(unittest.TestCase):
    def setUp(self):
        #self.parser = build_parser(echo, foo=[hello, howdy])
        self.parser = ArghParser()
        self.parser.add_commands([echo, plain_echo])
        self.parser.add_commands([hello, howdy], namespace='greet')

    def _call_cmd(self, command_string):
        args = command_string.split() if command_string else command_string
        try:
            return self.parser.dispatch(args)
        except SystemExit:
            self.fail('Argument parsing failed')

    def assert_cmd_prints(self, command_string, expected_result):
        """Executes given command using given parser and asserts that it prints
        given value.
        """
        result = self._call_cmd(command_string)
        self.assertEqual(result, expected_result)

    def assert_cmd_fails(self, command_string):
        # TODO: suppress printing errors by the ArgumentParser
        func = lambda: self.parser.dispatch(command_string.split())
        self.assertRaises(SystemExit, func)

    def test_argv(self):
        _argv = sys.argv
        sys.argv = sys.argv[:1] + ['echo', 'hi there']
        self.assert_cmd_prints(None, 'you said hi there')
        sys.argv = _argv

    def test_echo(self):
        "A simple command is resolved to a function."
        self.assert_cmd_prints('echo foo', 'you said foo')

    def test_plain_signature(self):
        "Arguments can be passed to the function without a Namespace instance."
        self.assert_cmd_prints('plain-echo bar', 'you said bar')

    def test_bare_namespace(self):
        "A command can be resolved to a function, to a namespace."
        self.assert_cmd_fails('greet')
        self.assert_cmd_fails('greet --name=world')

    def test_namespaced_function(self):
        "A subcommand is resolved to a function."
        self.assert_cmd_prints('greet hello', u'Hello world!')
        self.assert_cmd_prints('greet hello --name=John', u'Hello John!')
        self.assert_cmd_fails('greet hello John')
        self.assert_cmd_fails('greet howdy --name=John')
        self.assert_cmd_prints('greet howdy John', u'Howdy John?')

# TODO: find a workaround (it keeps printing to stdout)
#    def test_help_alias(self):
#        self._call_cmd('help echo')
#        self.assertEqual(self._call_cmd('help echo'),
#                         self._call_cmd('echo --help'))
