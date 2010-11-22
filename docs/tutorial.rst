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
        do_something(host=args.host, port=args.port, noreload=args.noreload)

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
Note how they are assembled together by :meth:`argh.ArghParser.add_commands`:
two at root level and two within a namespace "www". This is the resulting
command-line interface:

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
and ``foo quux``. It is equivalent to this generic argparse code::

    import sys
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    foo_parser = subparsers.add_parser('foo')
    foo_subparsers = foo_parser.add_subparsers()

    foo_bar_parser = foo_subparsers.add_parser('bar')
    foo_bar_parser.set_defaults(function=bar)

    foo_quux_parser = foo_subparsers.add_parser('quux')
    foo_quux_parser.set_defaults(function=quux)

    args = parser.parse_args()
    print args.function(args)

The `help` command is always added automatically and displays the docstring:

    * ``help shell`` → ``shell --help``
    * ``help web serve`` → ``web serve --help``

.. note::

    You don't have to use :class:`argh.ArghParser`; the standard
    :class:`argparse.ArgumentParser` will do. You will just need to call
    stand-alone functions :func:`argh.add_commands` and :func:`argh.dispatch`
    instead of :class:`argh.ArghParser` methods.

Returning results
-----------------

Most commands print something. The traditional straightforward way is this::

    def foo(args):
        print('hello')
        print('world')

However, this approach has a couple of flaws:

    * it is difficult to test functions that print results: you are bound to
      doctests or need to mess with replacing stdout;
    * terminals and pipes frequently have different requirements for encoding,
      so Unicode output may break the pipe (e.g. ``$ foo.py test | wc -l``). Of
      course you don't want to do the checks on every `print` statement.

A good solution would be to collect the output in a list and bulk-process it at
the end. Actually you can simply return a list and `Argh` will take care of the
encoding::

    def foo(args):
        return ['hello', 'world']

.. note::
    
    If you return a string, it is printed as is. A list or tuple is iterated
    and printed line by line. This is how :func:`dispatcher <argh.dispatch>`
    works.

This is fine, but what about non-linear code with if/else, exceptions and
interactive promts? Well, you don't need to manage the stack of results within
the function. Just convert it to a generator and `Argh` will do the rest::

    def foo(args):
        yield 'hello'
        yield 'world'

Syntactically this is exactly the same as the first example, only with `yield`
instead of `print`. But the function becomes much more flexible.

.. hint::

    If your command is likely to output Unicode and be used in pipes, you
    should definitely use the last approach.

Exceptions
----------

Usually you only want to display the traceback on unexpected exceptions. If you
know that something can be wrong, you'll probably handle it this way::

    @arg('key')
    def show_item(args):
        try:
            item = items[args.key]
        except KeyError as error:
            print(e)    # hide the traceback
            sys.exit()  # bail out (unsafe!)
        else:
            ... do something ...
            print(item)

This works but the print-and-exit tasks are repetitive; moreover, there are
cases when you don't want to raise `SystemExit` and just want to collect the
output in a uniform way. Use :class:`~argh.CommandError`::

    @arg('key')
    def show_item(args):
        try:
            item = items[args.key]
        except KeyError as error:
            raise CommandError(error)  # bail out, hide traceback
        else:
            ... do something ...
            yield item

`Argh` will wrap this exception and choose the right way to display its
message (depending on how :func:`argh.dispatch` was called).
