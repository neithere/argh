Tutorial
========

`Argh` is a small library that provides several layers of abstraction on top
of `argparse`.  You are free to use any layer that fits given task best.
The layers can be mixed.  It is always possible to declare a command with
the  highest possible (and least flexible) layer and then tune the behaviour
with any of the lower layers including the native API of `argparse`.

Please make sure you have read the :doc:`quickstart` before proceeding.

Declaring Commands
------------------

The Natural Way
...............

If you are comfortable with the basics of Python, you already knew the natural
way of declaring CLI commands with `Argh` before even learning about the
existence of `Argh`.

Please read the following snippet carefully.  Is there any `Argh`-specific API?

::

    def my_command(
        alpha: str, beta: int = 1, *args, gamma: int, delta: bool = False
    ) -> list[str]:
        return [alpha, beta, args, gamma, delta]

The answer is: no.  This is a completely generic Python function.

Let's make this function available as a CLI command::

    import argh


    def my_command(
        alpha: str, beta: int = 1, *args, gamma: int, delta: bool = False
    ) -> list[str]:
        return [alpha, beta, args, gamma, delta]


    if __name__ == "__main__":
        argh.dispatch_commands([my_command], old_name_mapping_policy=False)

That's all.  You don't need to do anything else.

.. note::

    Note that we're using ``old_name_mapping_policy=False`` here and in some
    other examples.  This has to do with the recent changes in the default way
    Argh maps function arguments to CLI arguments.  We're currently in a
    transitional period.

    In most cases Argh can guess what you want but there are edge cases, and
    the `beta` argument is one of them.  It's a positional argument with
    default value.  Usually you will not need those but it's shown here for the
    sake of completeness.  Argh does not know how you want to treat it, so you
    should specify the name mapping policy explicitly.  This issue will go away
    when `BY_NAME_IF_KWONLY` becomes the default policy (v.1.0 or earlier).

    See :class:`~argh.assembling.NameMappingPolicy` for details.

When executed as ``./app.py my-command --help``, such application prints::

    usage: app.py my-command [-h] -g GAMMA [-d] alpha [beta] [args ...]

    positional arguments:
      alpha                 -
      beta                  1
      args                  -

    options:
      -h, --help            show this help message and exit
      -g GAMMA, --gamma GAMMA
                            -
      -d, --delta           False

Now let's take a look at how we would do it without `Argh`::

    import argparse


    def my_command(
        alpha: str, beta: int = 1, *args, gamma: int, delta: bool = False
    ) -> list[str]:
        return [alpha, beta, args, gamma, delta]


    if __name__ == "__main__":
        parser = argparse.ArgumentParser()

        subparser = parser.add_subparsers().add_parser("my-command")

        subparser.add_argument("alpha")
        subparser.add_argument("beta", default=1, nargs="?", type=int)
        subparser.add_argument("args", nargs="*")
        subparser.add_argument("-g", "--gamma")
        subparser.add_argument("-d", "--delta", default=False, action="store_true")

        ns = parser.parse_args()

        lines = my_command(ns.alpha, ns.beta, *ns.args, gamma=ns.gamma, delta=ns.delta)

        for line in lines:
            print(line)

Verbose, hardly readable, requires learning the API.  With `Argh` it's just a
single line in addition to your function.

`Argh` allows for more expressive and pythonic code because:

* everything is inferred from the function signature and type annotations;
* regular function arguments are represented as positional CLI arguments;
* varargs (``*args``) are represented as a "zero or more" positional CLI argument;
* kwonly (keyword-only arguments, see :pep:`3102`) are represented as named CLI
  arguments;

  * keyword-only arguments with a `bool` default value are considered flags
    (AKA toggles) and their presence triggers the action `store_true` (or
    `store_false`).

* you can ``print()`` but you don't have to — the return value will be printed
  for you; it can even be an iterable (feel free to ``yield`` too), then each
  element will be printed on its own line.

Hey, that's a lot for such a simple case!  But then, that's why the API feels
natural: `argh` does a lot of work for you.

Well, there's nothing more elegant than a simple function.  But simplicity
comes at a cost in terms of flexibility.  Fortunately, `argh` doesn't stay in
the way and offers less natural but more powerful tools.

Annotations
...........

Since v.0.31 `Argh` can use type annotations to infer the argument types and
some other properties.  This approach will eventually replace the `@arg`
decorator.

Inferring the type
~~~~~~~~~~~~~~~~~~

Let's consider this example::

    def increment(n: int) -> int:
        return n + 1

The `n` argument will be automatically converted to `int`.

Currently supported types are:

- `str`
- `int`
- `float`
- `bool`

Inferring choices
~~~~~~~~~~~~~~~~~

Use `Literal` to specify the choices::

    from typing import Literal
    import argh

    def greet(name: Literal["Alice", "Bob"]) -> str:
        return f"Hello, {name}!"

    argh.dispatch_command(greet)

Let's explore this CLI::

    $ ./greet.py foo
    usage: greet.py [-h] {Alice,Bob}
    greet.py: error: argument name: invalid choice: 'foo' (choose from 'Alice', 'Bob')

    $ ./greet.py Alice
    Hello, Alice!

Inferring nargs and nested type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's another example::

    def summarise(numbers: list[int]) -> int:
        return sum(numbers)

    argh.dispatch_command(summarise)

Let's call it::

    $ ./app.py 1 2 3
    6

The ``list[int]`` hint was interpreted as ``nargs="+"`` + ``type=int``.

Please note that this part of the API is experimental and may change in the
future releases.

Documenting Your Commands
.........................

The function's docstring is automatically included in the help message.
When the script is called as ``./app.py my-command --help``, the docstring
is displayed along with a short overview of the arguments.

In many cases it's a good idea do add extra documentation per argument.
Extended argument declaration can be helpful in that case.

Extended Argument Declaration
.............................

.. note::

    This section will be out of date soon.  Typing hints will be used for all
    the cases described here including argument help.

When function signature isn't enough to fine-tune the argument declarations,
the :class:`~argh.decorators.arg` decorator comes in handy::

    @arg("path", help="file to load")
    @arg("--input-format", help="'json' or 'yaml'")
    def load_to_db(path: str, input_format: str = "json") -> None:
        data = loaders[input_format].load(path)

In this example we have declared a function with arguments `path` and `format`
and then extended their declarations with help messages.

The decorator mostly mimics `argparse`'s add_argument_.  The `name_or_flags`
argument must match function signature, that is:

1. ``path`` and ``--format`` map to ``func(path)`` and ``func(format="x")``
   respectively (short name like ``-f`` can be omitted);
2. a name that doesn't map to anything in function signature is not allowed.

.. _add_argument: http://docs.python.org/dev/library/argparse.html#argparse.ArgumentParser.add_argument

The decorator doesn't modify the function's behaviour in any way.

Sometimes the function is not likely to be used other than as a CLI command
and all of its arguments are duplicated with decorators.  Not very DRY.
In this case ``**kwargs`` can be used as follows::

    @arg("number", default=0, help="the number to increment")
    def increment(**kwargs) -> int:
        return kwargs["number"] + 1

In other words, if ``**something`` is in the function signature, extra
arguments are **allowed** to be specified via decorators; they all go into that
very dictionary.

Mixing ``**kwargs`` with straightforward signatures is also possible::

    @arg("--bingo")
    def cmd(foo: str, bar: int = 1, *maybe, **extra) -> ...:
        return ...

.. note::

   It is not recommended to mix ``*args`` with extra *positional* arguments
   declared via decorators because the results can be pretty confusing (though
   predictable).  See `argh` tests for details.

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

If the application has too many commands, they can be grouped::

    argh.add_commands(parser, [serve, ping], group_name="www")

The resulting CLI is as follows::

    $ ./app.py www {serve,ping}

See :doc:`subparsers` for the gory details.

Dispatching Commands
--------------------

The last thing is to actually parse the arguments and call the relevant command
(function) when our module is called as a script::

    if __name__ == "__main__":
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

Class Methods
.............

All kinds of class methods are supported as commands::

    class Commands:
        def instance_method(self) -> None:
            ...

        @classmethod
        def class_method(cls) -> None:
            ...

        @staticmethod
        def static_method() -> None:
            ...

    argh.dispatch_commands([
        Commands().instance_method,
        Commands.class_method,
        Commands.static_method
    ])

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


    app = EntryPoint("my cool app")

    @app
    def foo() -> str:
        return "hello"

    @app
    def bar() -> str:
        return "bye"


    if __name__ == "__main__":
        app()

Single-command application
--------------------------

There are cases when the application performs a single task and it perfectly
maps to a single command. The method above would require the user to type a
command like ``check_mail.py check --now`` while ``check_mail.py --now`` would
suffice. In such cases :func:`~argh.assembling.add_commands` should be replaced
with :func:`~argh.assembling.set_default_command`::

    def main() -> int:
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

    def foo() -> None:
        print("hello")
        print("world")

It works just fine.  However, there are cases when you would prefer a clean
function with a return value instead of a side effect:

* writing tests for the function without `capturing stdout`_ or using doctest_;
* reusing the function for some other purpose: wrapping in another CLI
  endpoint, exposing it via HTTP API, etc.

.. _capturing stdout: https://docs.pytest.org/en/7.1.x/how-to/capture-stdout-stderr.html
.. _doctest: https://docs.python.org/3/library/doctest.html

Good news: you can stick to the return value; Argh will redirect it to `stdout`
for you.  If it's a string, it will be printed verbatim.  If it's a sequence,
each item will be printed on its own line.  This works with generators too.

The following functions are equivalent if dispatched with Argh::

    def foo() -> str:
        print("hello\nworld")

    def foo() -> str:
        return "hello\nworld"

    def foo() -> list:
        return ["hello", "world"]

    def foo() -> list:
        yield "hello"
        yield "world"

Exceptions
----------

Usually you only want to display the traceback on unexpected exceptions. If you
know that something can be wrong, you'll probably handle it this way::

    def show_item(key: str) -> None:
        try:
            item = items[key]
        except KeyError as error:
            print(e)    # hide the traceback
            sys.exit(1)  # bail out (unsafe!)
        else:
            ... do something ...
            print(item)

This works, but the print-and-exit tasks are repetitive.
Instead, you can use :class:`~argh.exceptions.CommandError`::

    def show_item(key: str) -> str:
        try:
            item = items[key]
        except KeyError as error:
            raise CommandError(error)  # bail out, hide traceback
        else:
            ... do something ...
            return item

`Argh` will wrap this exception and choose the right way to display its
message (depending on how :func:`~argh.dispatching.dispatch` was called),
then exit with exit status 1 (indicating failure).

Decorator :func:`~argh.decorators.wrap_errors` reduces the code even further::

    @wrap_errors([KeyError])  # show error message, hide traceback
    def show_item(key: str) -> str:
        return items[key]     # raise KeyError

Of course it should be used with care in more complex commands.

The decorator accepts a list as its first argument, so multiple commands can be
specified.  It also allows plugging in a preprocessor for the caught errors::

    @wrap_errors(processor=lambda excinfo: "ERR: {0}".format(excinfo))
    def func() -> None:
        raise CommandError("some error")

The command above will print `ERR: some error`.

If you want to print and exit while still indicating the command completed
successfully, you can pass an optional `code` argument to the
:class:`~argh.exceptions.CommandError`::

    def show_item(key: str) -> str:
        try:
            item = items[key]
        except KeyError as error:
            raise CommandError(error, code=0)  # bail out, but exit with status 0
        else:
            ... do something ...
            return item

You can also pass any other code in order to exit with a specific error status.

Packaging
---------

.. warning::

    this section is outdated.  For modern instructions please refer to
    https://setuptools.pypa.io/en/latest/userguide/entry_point.html

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
