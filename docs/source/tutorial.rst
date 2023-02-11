Tutorial
~~~~~~~~

`Argh` is a small library that provides several layers of abstraction on top
of `argparse`.  You are free to use any layer that fits given task best.
The layers can be mixed.  It is always possible to declare a command with
the  highest possible (and least flexible) layer and then tune the behaviour
with any of the lower layers including the native API of `argparse`.

Dive In
-------

Assume we need a CLI application which output is modulated by arguments:

.. code-block:: bash

    $ ./greet.py
    Hello unknown user!

    $ ./greet.py --name John
    Hello John!

This is our business logic:

.. code-block:: python

    def main(name='unknown user'):
        return 'Hello {0}!'.format(name)

That was plain Python, nothing CLI-specific.
Let's convert the function into a complete CLI application::

    argh.dispatch_command(main)

Done.  Dead simple.

What about multiple commands?  Easy::

    argh.dispatch_commands([load, dump])

And then call your script like this::

    $ ./app.py dump
    $ ./app.py load fixture.json
    $ ./app.py load fixture.yaml --format=yaml

I guess you get the picture.  The commands are **ordinary functions**
with ordinary signatures:

* Declare them somewhere, dispatch them elsewhere.  This ensures **loose
  coupling** of components in your application.
* They are **natural** and pythonic. No fiddling with the parser and the
  related intricacies like ``action='store_true'`` which you could never
  remember.

Still, there's much more to commands than this.

The examples above raise some questions, including:

* do we have to ``return``, or ``print`` and ``yield`` are also supported?
* what's the difference between ``dispatch_command()``
  and ``dispatch_commands()``?  What's going on under the hood?
* how do I add help for each argument?
* how do I access the parser to fine-tune its behaviour?
* how to keep the code as DRY as possible?
* how do I expose the function under custom name and/or define aliases?
* how do I have values converted to given type?
* can I use a namespace object instead of the natural way?

Just read on.

Declaring Commands
------------------

The Natural Way
...............

You've already learned the natural way of declaring commands before even
knowing about `argh`::

    def my_command(alpha, beta=1, gamma=False, *delta):
        return

When executed as ``app.py my-command --help``, such application prints::

    usage: app.py my-command [-h] [-b BETA] [-g] alpha [delta [delta ...]]

    positional arguments:
      alpha
      delta

    optional arguments:
      -h, --help            show this help message and exit
      -b BETA, --beta BETA
      -g, --gamma

The same result can be achieved with this chunk of `argparse` code (with the
exception that in `argh` you don't immediately modify a parser but rather
declare what's to be added to it later)::

    parser.add_argument('alpha')
    parser.add_argument('-b', '--beta', default=1, type=int)
    parser.add_argument('-g', '--gamma', default=False, action='store_true')
    parser.add_argument('delta', nargs='*')

Verbose, hardly readable, requires learning another API.

`Argh` allows for more expressive and pythonic code because:

* everything is inferred from the function signature;
* arguments without default values are interpreted as required positional
  arguments;
* arguments with default values are interpreted as options;

  * options with a `bool` as default value are considered flags and their
    presence triggers the action `store_true` (or `store_false`);
  * values of options that don't trigger actions are coerced to the same type
    as the default value;

* the ``*args`` entry (function's positional arguments) is interpreted as
  a single argument with 0..n values.

Hey, that's a lot for such a simple case!  But then, that's why the API feels
natural: `argh` does a lot of work for you.

Well, there's nothing more elegant than a simple function.  But simplicity
comes at a cost in terms of flexibility.  Fortunately, `argh` doesn't stay in
the way and offers less natural but more powerful tools.

Documenting Your Commands
.........................

The function's docstring is automatically included in the help message.
When the script is called as ``./app.py my-command --help``, the docstring
is displayed along with a short overview of the arguments.

In many cases it's a good idea do add extra documentation per argument.
Extended argument declaration can be helpful in that case.

Extended Argument Declaration
.............................

When function signature isn't enough to fine-tune the argument declarations,
the :class:`~argh.decorators.arg` decorator comes in handy::

    @arg('path', help='file to load')
    @arg('--format', help='json or yaml')
    def load(path, format='yaml'):
        return loaders[format].load(path)

In this example we have declared a function with arguments `path` and `format`
and then extended their declarations with help messages.

The decorator mostly mimics `argparse`'s add_argument_.  The `name_or_flags`
argument must match function signature, that is:

1. ``path`` and ``--format`` map to ``func(path)`` and ``func(format='x')``
   respectively (short name like ``-f`` can be omitted);
2. a name that doesn't map to anything in function signature is not allowed.

.. _add_argument: http://docs.python.org/dev/library/argparse.html#argparse.ArgumentParser.add_argument

The decorator doesn't modify the function's behaviour in any way.

Sometimes the function is not likely to be used other than as a CLI command
and all of its arguments are duplicated with decorators.  Not very DRY.
In this case ``**kwargs`` can be used as follows::

    @arg('number', default=0, help='the number to increment')
    def increment(**kwargs):
        return kwargs['number'] + 1

In other words, if ``**something`` is in the function signature, extra
arguments are **allowed** to be specified via decorators; they all go into that
very dictionary.

Mixing ``**kwargs`` with straightforward signatures is also possible::

    @arg('--bingo')
    def cmd(foo, bar=1, *maybe, **extra):
        return ...

.. note::

   It is not recommended to mix ``*args`` with extra *positional* arguments
   declared via decorators because the results can be pretty confusing (though
   predictable).  See `argh` tests for details.

Namespace Objects
.................

The default approach of `argparse` is similar to ``**kwargs``: the function
expects a single object and the CLI arguments are defined elsewhere.

In order to dispatch such "argparse-style" command via `argh`, you need to
tell the latter that the function expects a namespace object.  This is done by
wrapping the function into the :func:`~argh.decorators.expects_obj` decorator::

    @expects_obj
    def cmd(args):
        return args.foo

This way arguments cannot be defined in the Natural Way but the
:class:`~argh.decorators.arg` decorator works as usual.

.. note::

   In both cases — ``**kwargs``-only and `@expects_obj` — the arguments
   **must** be declared via decorators or directly via the `argparse` API.
   Otherwise the command has zero arguments (apart from ``--help``).

Assembling Commands
-------------------

.. note::

    `Argh` decorators introduce a declarative mode for defining commands. You
    can access the `argparse` API after a parser instance is created.

After the commands are declared, they should be assembled within a single
argument parser.  First, create the parser itself::

    parser = argparse.ArgumentParser()

Add a couple of commands via :func:`~argh.assembling.add_commands`::

    argh.add_commands(parser, [load, dump])

The commands will be accessible under the related functions' names::

    $ ./app.py {load,dump}

Subcommands
...........

If the application has too many commands, they can be grouped into namespaces::

    argh.add_commands(parser, [serve, ping], namespace='www',
                      title='Web-related commands')

The resulting CLI is as follows::

    $ ./app.py www {serve,ping}

See :doc:`subparsers` for the gory details.

Dispatching Commands
--------------------

The last thing is to actually parse the arguments and call the relevant command
(function) when our module is called as a script::

    if __name__ == '__main__':
        argh.dispatch(parser)

The function :func:`~argh.dispatching.dispatch` uses the parser to obtain the
relevant function and arguments; then it converts arguments to a form
digestible by this particular function and calls it.  The errors are wrapped
if required (see below); the output is processed and written to `stdout`
or a given file object.  Special care is given to terminal encoding.  All this
can be fine-tuned, see API docs.

A set of commands can be assembled and dispatched at once with a shortcut
:func:`~argh.dispatching.dispatch_commands` which isn't as flexible as the
full version described above but helps reduce the code in many cases.
Please refer to the API documentation for details.

Modular Application
...................

As you can see, with `argh` the CLI application consists of three parts:

1. declarations (functions and their arguments);
2. assembling (a parser is constructed with these functions);
3. dispatching (input → parser → function → output).

This clear separation makes a simple script just a bit more readable,
but for a large application this is extremely important.

Also note that the parser is standard.
It's OK to call :func:`~argh.dispatching.dispatch` on a custom subclass
of `argparse.ArgumentParser`.

By the way, `argh` ships with :class:`~argh.helpers.ArghParser` which
integrates the assembling and dispatching functions for DRYness.

Entry Points
............

.. versionadded:: 0.25

The normal way is to declare commands, then assemble them into an entry
point and then dispatch.

However, It is also possible to first declare an entry point and then
register the commands with it right at command declaration stage.

The commands are assembled together but the parser is not created until
dispatching.

To do so, use :class:`~argh.dispatching.EntryPoint`::

   from argh import EntryPoint


   app = EntryPoint('my cool app')

   @app
   def foo():
       return 'hello'

   @app
   def bar():
       return 'bye'


   if __name__ == '__main__':
       app()

Single-command application
--------------------------

There are cases when the application performs a single task and it perfectly
maps to a single command. The method above would require the user to type a
command like ``check_mail.py check --now`` while ``check_mail.py --now`` would
suffice. In such cases :func:`~argh.assembling.add_commands` should be replaced
with :func:`~argh.assembling.set_default_command`::

    def main():
        return 1

    argh.set_default_command(parser, main)

There's also a nice shortcut :func:`~argh.dispatching.dispatch_command`.
Please refer to the API documentation for details.

Subcommands + Default Command
-----------------------------

.. versionadded:: 0.26

It's possible to augment a single-command application with nested commands:

.. code-block:: python

    p = ArghParser()
    p.add_commands([foo, bar])
    p.set_default_command(foo)    # could be a `quux`

Generated help
--------------

`Argparse` takes care of generating nicely formatted help for commands and
arguments. The usage information is displayed when user provides the switch
``--help``. However `argparse` does not provide a ``help`` *command*.

`Argh` always adds the command ``help`` automatically:

    * ``help shell`` → ``shell --help``
    * ``help web serve`` → ``web serve --help``

See also `<#documenting-your-commands>`_.

Returning results
-----------------

Most commands print something. The traditional straightforward way is this::

    def foo():
        print('hello')
        print('world')

However, this approach has a couple of flaws:

    * it is difficult to test functions that print results: you are bound to
      doctests or need to mess with replacing stdout;
    * terminals and pipes frequently have different requirements for encoding,
      so Unicode output may break the pipe (e.g. ``$ foo.py test | wc -l``). Of
      course you don't want to do the checks on every `print` statement.

Good news: if you return a string, `Argh` will take care of the encoding::

    def foo():
        return 'привет'

But what about multiple print statements?  Collecting the output in a list
and bulk-processing it at the end would suffice.  Actually you can simply
return a list and `Argh` will take care of it::

    def foo():
        return ['hello', 'world']

.. note::

    If you return a string, it is printed as is.  A list or tuple is iterated
    and printed line by line. This is how :func:`dispatcher
    <argh.dispatching.dispatch>` works.

This is fine, but what about non-linear code with if/else, exceptions and
interactive prompts? Well, you don't need to manage the stack of results within
the function. Just convert it to a generator and `Argh` will do the rest::

    def foo():
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

    def show_item(key):
        try:
            item = items[key]
        except KeyError as error:
            print(e)    # hide the traceback
            sys.exit()  # bail out (unsafe!)
        else:
            ... do something ...
            print(item)

This works, but the print-and-exit tasks are repetitive; moreover, there are
cases when you don't want to raise `SystemExit` and just need to collect the
output in a uniform way. Use :class:`~argh.exceptions.CommandError`::

    def show_item(key):
        try:
            item = items[key]
        except KeyError as error:
            raise CommandError(error)  # bail out, hide traceback
        else:
            ... do something ...
            return item

`Argh` will wrap this exception and choose the right way to display its
message (depending on how :func:`~argh.dispatching.dispatch` was called).

Decorator :func:`~argh.decorators.wrap_errors` reduces the code even further::

    @wrap_errors([KeyError])  # show error message, hide traceback
    def show_item(key):
        return items[key]     # raise KeyError

Of course it should be used with care in more complex commands.

The decorator accepts a list as its first argument, so multiple commands can be
specified.  It also allows plugging in a preprocessor for the caught errors::

    @wrap_errors(processor=lambda excinfo: 'ERR: {0}'.format(excinfo))
    def func():
        raise CommandError('some error')

The command above will print `ERR: some error`.

Packaging
---------

So, you've done with the first version of your `Argh`-powered app.  The next
step is to package it for distribution.  How to tell `setuptools` to create
a system-wide script?  A simple example sums it up:

.. code-block:: python

    from setuptools import setup, find_packages

    setup(
        name = 'myapp',
        version = '0.1',
        entry_points = {'console_scripts': ['myapp = myapp:main']},
        packages = find_packages(),
        install_requires = ['argh'],
    )

This creates a system-wide `myapp` script that imports the `myapp` module and
calls a `myapp.main` function.

More complex examples can be found in this contributed repository:
https://github.com/illumin-us-r3v0lution/argh-examples
