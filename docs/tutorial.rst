Tutorial
========

Here's an example::

    # coding: utf-8
    from argh import arg, ArghParser

    # define a couple of non-web commands

    def shell(args):
        "Runs the interactive shell."    # ← the command documentation
        run_the_interactive_shell()

    @arg('file', help='fixture to load')  # ← a command argument
    def load(args):
        "Loads a JSON fixture from given file."
        print json.load(args.file)

    # define a pair of web server commands with a handful of arguments

    @arg('--host', default='127.0.0.1', help='The host')
    @arg('--port', default=6060, help='The port')
    @arg('--noreload', default=False, help='Do not use autoreloader')
    def serve(args):
        "Runs a simple webserver."
        do_something(host=args.host)

    def serve_rest(args):
        "Run some REST service... whatever."
        do_something()

    # now assemble all the commands — web-related and miscellaneous — within
    # a single argument parser

    parser = ArghParser()  # ← this is an ArgumentParser subclass
    parser.add_commands([shell, load])
    parser.add_commands([serve, serve_rest], namespace='www',
                        title='Web-related commands')

    if __name__=='__main__':
        parser.dispatch()

The example above defines four commands: `shell`, `load`, `serve` and `serve-rest`.
Note how they are assembled together in the last :func:`make_parser` call: two
commands as arguments and two as a keyword argument `web`. This is the
resulting command-line interface:

    * ``./prog.py shell``
    * ``./prog.py load prancing_ponies.json``
    * ``./prog.py www serve-rest``
    * ``./prog.py www serve --port 6060 --noreload``

See what's happening here?

The statement ``parser.add_commands([bar, quux])`` builds two subparsers named
`bar` and `quux`.

Now consider this expression::

    parser = ArghParser()
    parser.add_commands([bar, quux], namespace='foo')
    parser.dispatch()

It produces a command hierarchy for the command-line expressions ``foo bar``
and ``foo quux``. It is roughly equivalent to this generic argparse code::

    import sys
    from argparse import ArgumentParser

    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()
    foo_parser = subparsers.add_parser('foo')
    foo_subparsers = foo_parser.add_subparsers()
    foo_bar_parser = foo_subparsers.add_parser('bar')
    foo_bar_parser.set_defaults(function=bar)
    args = p.parse_args(sys.argv[1:])
    print args.function(args)

The `help` command is always added automatically and displays the docstring:

    * ``help shell`` → ``shell --help``
    * ``help web serve`` → ``web serve --help``

.. note::

    You don't have to use :class:`ArghParser`; the standard
    :class:`argparse.ArgumentParser` will do. You will just need to call
    stand-alone functions :func:`add_commands` and :func:`dispatch` instead of
    :class:`ArghParser` methods.

