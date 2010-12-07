Tutorial
========

`Argh` is a small library that provides several layers of abstraction on top of
`argparse`. You are free to use any layer that fits given task best. The layers
can be mixed. It is always possible to declare a command with the highest
possible (and least flexible) layer — the :func:`~argh.decorators.command`
decorator — and then tune the behaviour with any of the lower layers:
:func:`~argh.decorators.arg`, :func:`~argh.helpers.add_commands`,
:func:`~argh.helpers.dispatch` or directly via the `argparse` API.

Dive in
-------

Defining and running commands is dead simple::

    from argh import *
    
    @command
    def load(path, format='json'):
        print loaders[format].load(path)

    p = ArghParser()
    p.add_commands([load])
    p.dispatch()

And then call your script like this::

    $ ./script.py load fixture.json
    $ ./script.py load fixture.yaml --format=yaml

I guess you get the picture. Still, there's much more to commands than this.
You'll want to provide help per command and per argument, you will want to
specify aliases, data types, namespaces and... just read on.

Declaring commands
------------------

Let's start with an almost real-life example where we define some commands.
First, import :class:`~argh.helpers.ArghParser` (an extended version of the
standard :class:`argparse.ArgumentParser`) and the decorator
:func:`~argh.decorators.arg` which we'll use to tell the parser what arguments
should given function accept::

    # coding: utf-8
    from argh import arg, ArghParser

Now define a command. It is just a function that may accept arguments. By
default it should accept a namespace object::

    def shell(args):
        "Runs the interactive shell."    # ← the command documentation
        run_the_interactive_shell()

That command didn't actually have any arguments. Let's create another one that
does::

    @arg('file', help='fixture to load')  # ← a command argument
    def load(args):
        "Loads a JSON fixture from given file."
        print json.load(args.file)

The command ``load`` will now require a positional argument `file`. We'll run
it later this way::

    $ ./prog.py load fixture.json

Here's another command with a handful of arguments, all of them optional::

    @arg('--host', default='127.0.0.1', help='The host')
    @arg('--port', default=6060, help='The port')
    @arg('--noreload', default=False, help='Do not use autoreloader')
    def serve(args):
        "Runs a simple webserver."
        do_something(host=args.host, port=args.port, noreload=args.noreload)

...and the fourth command will follow. It's pretty simple. Note that it too has
a docstring that will show up when we call our script with the ``--help``
switch::

    def serve_rest(args):
        "Run some REST service... whatever."
        do_something()

At this point we have four functions: `shell`, `load`, `serve` and
`serve_rest`. They are not "commands" yet because we don't even have a parser
or dispatcher. The script must know how to interpret the arguments passed in by
the user.

Assembling commands
-------------------

.. note::

    `Argh` decorators introduce a declarative mode for defining commands. You
    can access the `argparse` API after a parser instance is created.

Our next step is to assemble all the commands — web-related and miscellaneous —
within a single argument parser. First, create the parser itself::

    parser = ArghParser()  # ← this is an ArgumentParser subclass

Inform it of the first two commands::

    parser.add_commands([shell, load])

These will be accessible under the related functions' names.

Then add the web-related commands (note the difference)::

    parser.add_commands([serve, serve_rest],
                         namespace='www',
                         title='Web-related commands')

We have just created a couple of *subcommands* under the namespace "www". The
`title` keyword is for documentation purposes (see
:func:`~argh.helpers.add_commands` documentation).

The last thing is to actually parse the arguments and call the relevant command
(function) when our module is called as a script::

    if __name__=='__main__':
        parser.dispatch()

Great! We have created a fully working script with two simple commands
(``shell`` and ``load``) and two subcommands (``www serve`` and ``www
serve-rest``).

Note how they are assembled together by
:meth:`~argh.helpers.ArghParser.add_commands`: two at root level and two within
a namespace "www". This is the resulting command-line interface::

    $ ./prog.py shell
    $ ./prog.py load prancing_ponies.json
    $ ./prog.py www serve-rest
    $ ./prog.py www serve --port 6060 --noreload

Subparsers
----------

The statement ``parser.add_commands([bar, quux])`` builds two subparsers named
`bar` and `quux`. A "subparser" is an argument parser bound to a namespace. In
other words, it works with everything after a certain positional argument.
`Argh` implements commands by creating a subparser for every function.

Again, here's how we create two subparsers for commands ``foo`` and ``bar``::

    parser = ArghParser()
    parser.add_commands([bar, quux])
    parser.dispatch()

The equivalent code without `Argh` would be::

    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    foo_parser = subparsers.add_parser('foo')
    foo_parser.set_defaults(function=foo)

    foo_parser = subparsers.add_parser('bar')
    foo_parser.set_defaults(function=bar)

    args = parser.parse_args()
    print args.function(args)

Now consider this expression::

    parser = ArghParser()
    parser.add_commands([bar, quux], namespace='foo')
    parser.dispatch()

It produces a command hierarchy for the command-line expressions ``foo bar``
and ``foo quux``. This involves "subsubparsers". Without `Argh` you would need
to write something like this (generic argparse API)::

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

.. note::

    You don't have to use :class:`~argh.helpers.ArghParser`; the standard
    :class:`argparse.ArgumentParser` will do. You will just need to call
    stand-alone functions :func:`~argh.helpers.add_commands` and
    :func:`~argh.helpers.dispatch` instead of :class:`~argh.helpers.ArghParser`
    methods.

Generated help
--------------

`Argparse` takes care of generating nicely formatted help for commands and
arguments. The usage information is displayed when user provides the switch
``--help``. However `argparse` does not provide a ``help`` *command*.

`Argh` always adds the command ``help`` automatically. It displays the
docstring:

    * ``help shell`` → ``shell --help``
    * ``help web serve`` → ``web serve --help``

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
    and printed line by line. This is how :func:`dispatcher
    <argh.helpers.dispatch>` works.

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
output in a uniform way. Use :class:`~argh.exceptions.CommandError`::

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
message (depending on how :func:`~argh.helpers.dispatch` was called).
