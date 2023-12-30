Argh: The Natural CLI
=====================

.. image:: https://github.com/neithere/argh/actions/workflows/lint-and-test.yml/badge.svg
    :target: https://github.com/neithere/argh/actions/workflows/lint-and-test.yml

.. image:: https://img.shields.io/pypi/format/argh.svg
    :target: https://pypi.python.org/pypi/argh

.. image:: https://img.shields.io/pypi/status/argh.svg
    :target: https://pypi.python.org/pypi/argh

.. image:: https://img.shields.io/pypi/v/argh.svg
    :target: https://pypi.python.org/pypi/argh

.. image:: https://img.shields.io/pypi/pyversions/argh.svg
    :target: https://pypi.python.org/pypi/argh

.. image:: https://img.shields.io/pypi/dd/argh.svg
    :target: https://pypi.python.org/pypi/argh

.. image:: https://readthedocs.org/projects/argh/badge/?version=stable
    :target: http://argh.readthedocs.org/en/stable/

.. image:: https://readthedocs.org/projects/argh/badge/?version=latest
    :target: http://argh.readthedocs.org/en/latest/

Building a command-line interface?  Found yourself uttering "argh!" while
struggling with the API of `argparse`?  Don't like the complexity but need
the power?

.. epigraph::

    Everything should be made as simple as possible, but no simpler.

    -- Albert Einstein (probably)

`Argh` is a smart wrapper for `argparse`.  `Argparse` is a very powerful tool;
`Argh` just makes it easy to use.

In a nutshell
-------------

`Argh`-powered applications are *simple* but *flexible*:

:Pythonic:
    Commands are plain Python functions.  No CLI-specific API to learn.

:Modular:
    Declaration of commands can be decoupled from assembling and dispatching;

:Reusable:
    Endpoint functions can be used directly outside of CLI context;

:Static typing friendly:
    100% of the code including endpoint functions can be type-checked.
    Argh relies on type annotations while other libraries tend to rely on
    decorators and namespace objects, sometimes even mangling function
    signatures;

:Layered:
    The complexity of code raises with requirements;

:Transparent:
    The full power of argparse is available whenever needed;

:Namespaced:
    Nested commands are a piece of cake, Argh isolates the complexity of
    subparsers;

:DRY:
    Don't Repeat Yourself.  The amount of boilerplate code is minimal.
    Among other things, `Argh` will:

    * infer command name from function name;
    * infer arguments from function signature;
    * infer argument types, actions and much more from annotations.

:NIH free:
    `Argh` supports *completion*, *progress bars* and everything else by being
    friendly to excellent 3rd-party libraries.  No need to reinvent the wheel.

:Compact:
    No dependencies apart from Python's standard library.

Sounds good?  Check the :doc:`quickstart` and the :doc:`tutorial`!

Relation to argparse
--------------------

`Argh` is fully compatible with `argparse`.  You can mix `Argh`-agnostic and
`Argh`-aware code.  Just keep in mind that the dispatcher does some extra work
that a custom dispatcher may not do.

Installation
------------

::

    $ pip install argh

Examples
--------

Hello World
...........

A very simple application with one command:

.. code-block:: python

    import argh

    def main() -> str:
        return "Hello world"

    argh.dispatch_command(main)

Run it:

.. code-block:: bash

    $ ./app.py
    Hello world

Type Annotations
................

Type annotations are used to infer argument types:

.. code-block:: python

    def summarise(numbers: list[int]) -> int:
        return sum(numbers)

    argh.dispatch_command(summarise)

Run it (note that ``nargs="+"`` + ``type=int`` were inferred from the
annotation):

.. code-block:: bash

    $ ./app.py 1 2 3
    6

Multiple Commands
.................

An app with multiple commands:

.. code-block:: python

    import argh

    from my_commands import hello, echo

    argh.dispatch_commands([hello, echo])

Run it:

.. code-block:: bash

    $ ./app.py echo Hey
    Hey

Modularity
..........

A potentially modular application with more control over the process:

.. code-block:: python

    import argh

    # declaring:

    def echo(text):
        "Returns given word as is."
        return text

    def greet(name: str, *, greeting: str = "Hello") -> str:
        "Greets the user with given name. The greeting is customizable."
        return f"{greeting}, {name}!"

    # assembling:

    parser = argh.ArghParser()
    parser.add_commands([echo, greet])

    # dispatching:

    if __name__ == "__main__":
        parser.dispatch()

.. code-block:: bash

    $ ./app.py greet Andy
    Hello, Andy

    $ ./app.py greet Andy -g Arrrgh
    Arrrgh, Andy

Here's the auto-generated help for this application (note how the docstrings
are reused)::

    $ ./app.py --help

    usage: app.py {echo,greet} ...

    positional arguments:
        echo        Returns given word as is.
        greet       Greets the user with given name. The greeting is customizable.

...and for a specific command (an ordinary function signature is converted
to CLI arguments)::

    $ ./app.py --help greet

    usage: app.py greet [-g GREETING] name

    Greets the user with given name. The greeting is customizable.

    positional arguments:
      name

    optional arguments:
      -g GREETING, --greeting GREETING   'Hello'

(The help messages have been simplified a bit for brevity.)

Decorators
..........

`Argh` easily maps plain Python functions to CLI.  Sometimes this is not
enough; in these cases the powerful API of `argparse` is also available:

.. code-block:: python

    @arg("text", default="hello world", nargs="+", help="The message")
    def echo(text: str) -> None:
        print text

Please note that decorators will soon be fully replaced with annotations.

Links
-----

* `Project home page`_ (GitHub)
* `Documentation`_ (Read the Docs)
* `Package distribution`_ (PyPI)
* Questions, requests, bug reports, etc.:

  * `Issue tracker`_ (GitHub)
  * Direct e-mail (neithere at gmail com)

.. _project home page: http://github.com/neithere/argh/
.. _documentation: http://argh.readthedocs.org
.. _package distribution: http://pypi.python.org/pypi/argh
.. _issue tracker: http://github.com/neithere/argh/issues/

Author
------

Developed by Andrey Mikhaylenko since 2010.

See file `AUTHORS.rst` for a list of contributors to this library.

Support
-------

The fastest way to improve this project is to submit tested and documented
patches or detailed bug reports.

You can also `donate via Liberapay`_.  This may speed up development or simply
make the original author happy :)

.. _donate via Liberapay: https://liberapay.com/neithere/donate

Licensing
---------

Argh is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Argh is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Argh.  If not, see <http://gnu.org/licenses/>.
