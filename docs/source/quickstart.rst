Quick Start
===========

Command-Line Interface
----------------------

CLI is a very efficient way to interact with an application.
If GUI is like pointing your finger at things, then CLI is like talking.

Building a good CLI may require quite a bit of effort.  You need to connect two
worlds: your Python API and the command-line interface which has its own rules.

At a closer inspection you may notice that a CLI command is very similar to a function.
You have positional and named arguments, you pass them into the function and
get a return value — and the same happens with a command.  However, the mapping is not
exactly straightforward and a lot of boilerplate is required to make it work.

The intent of Argh is to radically streamline this function-to-CLI mapping.

We'll try to demonstrate it with a few examples here.

Passing name as positional argument
-----------------------------------

Assume we need a CLI application which output is modulated by arguments:

.. code-block:: bash

    $ ./greet.py
    Hello unknown user!

    $ ./greet.py John
    Hello John!

Let's start with a simple function:

.. code-block:: python

    def main(name: str = "unknown user") -> str:
        return f"Hello {name}!"

Now make it a CLI command:

.. code-block:: python

    #!/usr/bin/env python3

    import argh

    def main(name: str = "unknown user") -> str:
        return f"Hello {name}!"

    argh.dispatch_command(main, old_name_mapping_policy=False)

Save it as `greet.py` and try to run it::

    $ chmod +x greet.py
    $ ./greet.py
    Hello unknown user!

It works!  Now try passing arguments.  Use ``--help`` if unsure::

    $ ./greet.py --help

    usage: greet.py [-h] [name]

    positional arguments:
      name        'unknown user'

    options:
      -h, --help  show this help message and exit

Multiple positional arguments; limitations
------------------------------------------

You can add more positional arguments.  They are determined by their position
in the function signature::

    def main(first, second, third):
        print(f"second: {second}")

    main(1, 2, 3)  # prints "two: 2"

Same will happen if we dispatch this function as a CLI command::

    $ ./app.py 1 2 3
    two: 2

This is fine, but it's usually hard to remember the order of arguments when
their number is over three or so.

Moreover, you may want to omit the first one and specify the rest — but it's
impossible.  How would the computer know if the element you are skipping is
supposed to be the first, the last or somewhere in the middle?  There's no way.

If only it was possible to pass such arguments by name!

Indeed, a good command-line interface is likely to have one or two positional
arguments but the rest should be named.

In Python you can do it by calling your function this way::

    main(first=1, second=2, third=3)

In CLI named arguments are called "options".  Please see the next section to
learn how to use them.

Passing name as an option
-------------------------

Let's return to our small application and see if we can make the name
an "option" AKA named CLI argument, like this::

    $ ./greet.py --name John

In that case it's enough to make the function argument `name` "keyword-only"
(see :pep:`3102` for explanation)::

    def main(*, name: str = "unknown user") -> str:
        ...

We just took the previous function and added ``*,`` before the first argument.

Let's check how the app help now looks like::

    $ ./greet.py --help

    usage: greet.py [-h] [-n NAME]

    options:
      -h, --help            show this help message and exit
      -n NAME, --name NAME  'unknown user'

Positional vs options: recap
----------------------------

Here's a function with one positional argument and one "option"::

    def main(name: str, *, age: int = 0) -> str:
        ...

* All arguments to the left of ``*`` are considered positional.
* All arguments to the right of ``*`` are considered named (or "options").

Multiple Commands
-----------------

We used `argh.dispatch_command()` to run a single command.

In order to enable multiple commands we simply use a sister function
`argh.dispatch_commands()` and pass a list of functions to it::

    argh.dispatch_commands([load, dump])

Bam!  Now we can call our script like this::

    $ ./app.py dump
    $ ./app.py load fixture.json
    $ ./app.py load fixture.yaml --format=yaml
      \______/ \__/ \________________________/
       |        |    |
       |        |    `-- command arguments
       |        |
       |        `-- command name (function name)
       |
       `-- script file name

Typing Hints
------------

Typing hints are picked up when it makes sense too.  Consider this::

    def summarise(numbers: list[int]) -> int:
        return sum(numbers)

    argh.dispatch_command(summarise)

Call it::

    $ ./app 1 2 3
    6

It worked exactly as you would expect.  Argh looked at the annotation and
understood that you want a list of integers.  This information was then
reworded for `argparse`.

Quick Start Wrap-Up
-------------------

To sum up, the commands are **ordinary functions** with ordinary signatures:

* Declare them somewhere, dispatch them elsewhere.  This ensures **loose
  coupling** of components in your application.
* They are **natural** and pythonic. No fiddling with the parser and the
  related intricacies like ``action="store_true"`` which you could never
  remember.

Next: Tutorial
--------------

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

Please check the :doc:`tutorial` for answers.
