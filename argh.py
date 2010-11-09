# -*- coding: utf-8 -*-
"""
Agrh, argparse!
===============

Did you ever say "argh" trying to remember the details of optparse or argparse
API? If yes, this package may be useful for you. It provides a very simple
wrapper for argparse with support for hierarchical commands that can be bound
to modules or classes. Argparse can do it; argh makes it easy.

Usage
-----

Here's an example::

    from argh import arg, dispatch

    # define a couple of non-web commands

    def shell(args):
        "Runs the interactive shell."    # <- the command documentation
        run_the_interactive_shell(...)

    @arg('file', description='fixture to load')  # <- a command argument
    def load(args):
        "Loads a JSON fixture from given file."
        print json.load(args.file)

    # define a pair of web server commands with a handful of arguments

    @arg('host', default='127.0.0.1', description='The host')
    @arg('port', default=6060, description='The port')
    @arg('noreload', default=False, description='Do not use autoreloader')
    def serve(args):
        "Runs a simple webserver."
        do_something(host=args.host, ...)

    def serve_rest(args):
        "Run some REST service... whatever."
        do_something()

    # instantiate an ArgumentParser for the web-related commands
    # so they are grouped; this parser is standalone and can be used right away

    web_commands = make_parser(serve)

    # now assemble all the commands — web-related and miscellaneous — within a
    # single argument parser

    parser = make_parser(shell, load, web=web_commands)

    if __name__=='__main__':
        dispatch(parser)

The example above defines four commands: `shell`, `load`, `serve` and `rest`.
Note how they are assembled together in the last :func:`make_parser` call: two
commands as arguments and two as a keyword argument `web`. This is the
resulting command-line interface:

    * ``shell``
    * ``load prancing_ponies.json``
    * ``web serve_rest``
    * ``web serve -p 6060 --noreload``

See what's happening here?

The statement ``make_parser(bar, quux)`` builds an ArgumentParser with two
commands: `bar` and `quux`.

The statement ``make_parser(foo=make_parser(bar, quux))`` produces a command
hierarchy for the command-line expressions ``foo bar`` and ``foo quux``. It is
roughly equivalent to this generic argparse code::

    import sys
    from argparse import ArgumentParser

    def bar(args):
        return 'I am foobar!'

    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()
    foo_parser = subparsers.add_parser('foo')
    foo_subparsers = foo_parser.add_subparsers()
    foo_bar_parser = foo_subparsers.add_parser('bar')
    foo_bar_parser.set_defaults(function=bar)
    args = p.parse_args(sys.argv[1:])
    print args.function(args)

The `help` command is always added automatically and displays the docstring:

    * ``help shell``
    * ``help web serve``

API
---
"""
__all__ = ['arg', 'make_parser']
__version__ = '0.1.0'

from functools import wraps
import argparse


def arg(func):
    """Declares an argument for given function. Does not register the function
    anywhere, not does it modify the function in any way.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func.argh_args = getattr(func, 'argh_args', [])
        func.argh_args.append((args, kwargs))
        return func
    return wrapper

def make_parser(*commands, **subcommands):
    """Returns an ArgumentParser instance that can handle given commands and
    subcommands.

    :param commands:
        A list of functions. Each function *must* accept only one argument: the
        Namespace instance as returned by ArgumentParser. Any extra arguments
        must be defined by wrapping the function into :func:`arg`. The function
        names will be translated to command names.
    :param subcommands:
        A dictionary where names are

    Usage::

        def foo(args):
            print 'I am foo'
        def bar(args): pass
            print 'I am bar'
        top_level_cmds = foo, bar
        def quux(args): pass
            print 'I am baz/quux'
        # register commands: "foo", "bar", "baz quux"
        p = make_parser(*top_level_cmds, baz=quux)
        p.parse_args(sys.argv[1:])

    """
    raise NotImplementedError

def dispatch(args):
    raise NotImplementedError

if __name__=='__main__':
    import sys
    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()
    foo_parser = subparsers.add_parser('foo')
    foo_subparsers = foo_parser.add_subparsers()
    foo_bar_parser = foo_subparsers.add_parser('bar')
    def bar(args):
        return 'I am foobar!'
    foo_bar_parser.set_defaults(function=bar)
    args = p.parse_args(sys.argv[1:])
    print args.function(args)
