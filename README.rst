Argh: The Effortless CLI
========================

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

**The power of Argparse with plain Python functions!**

Building a command-line interface?  Found yourself uttering "argh!" while
struggling with the API of `argparse`?  Don't like the complexity but need
the power?

`Argh` builds on the power of `argparse` (which comes with Python) and makes it
really easy to use.  It eliminates the complex API and lets you "dispatch"
ordinary Python functions as CLI commands.

Installation
------------

::

    $ pip install argh

Example
-------

.. code-block:: python

    import argh

    def verify_paths(paths: list[str], *, verbose: bool = False):
        """
        Verify that all given paths exist.
        """
        for path in paths:
            if verbose:
                print(f"Checking {path}...")
            assert os.path.exists(path)

    argh.dispatch_command(verify_paths)

Now you can run the script like this:

.. code-block:: bash

    $ python app.py foo.txt bar/quux.txt

    $ python app.py foo.txt bar/quux.txt --verbose
    Checking foo.txt...
    Checking bar/quux.txt...

    $ python app.py -h
    usage: app.py [-h] [-v] [paths ...]

    Verify that all given paths exist.

    positional arguments:
      paths          -

    options:
      -h, --help     show this help message and exit
      -v, --verbose  False

Please check the documentation for examples of multiple commands, modularity,
help generation, advanced type annotations inspection, decorators and more:

* `Quick Start <https://argh.readthedocs.io/en/latest/quickstart.html>`_
* `Tutorial <https://argh.readthedocs.io/en/latest/tutorial.html>`_

Why Argh?
---------

`Argh`-powered applications are *simple* but *flexible*:

:Pythonic, KISS:
    Commands are plain Python functions.  Almost no CLI-specific API to learn.

:Reusable:
    Endpoint functions can be used directly outside of CLI context.

:Static typing friendly:
    100% of the code including endpoint functions can be type-checked.
    Argh is driven primarily by type annotations.

:DRY:
    Don't Repeat Yourself.  The amount of boilerplate code is minimal.
    Among other things, `Argh` will:

    * infer command name from function name;
    * infer arguments from function signature;
    * infer argument types, actions and much more from annotations.

:Modular:
    Declaration of commands can be decoupled from assembling and dispatching.

:Layered:
    The complexity of code raises with requirements.

:Transparent:
    You can directly access `argparse.ArgumentParser` if needed.

:Subcommands:
    Easily nested commands.  Argh isolates the complexity of subparsers.

:NIH free:
    `Argh` supports *completion*, *progress bars* and everything else by being
    friendly to excellent 3rd-party libraries.  No need to reinvent the wheel.

:Compact:
    No dependencies apart from Python's standard library.

Links
-----

See also the `project page on GitHub`_, `documentation`_ and `PyPI page`_.

.. _project page on GitHub: http://github.com/neithere/argh/
.. _documentation: http://argh.readthedocs.org
.. _PyPI page: http://pypi.python.org/pypi/argh

Author
------

Developed by Andrey Mikhaylenko since 2010.

See `contributors <https://argh.readthedocs.io/en/latest/contributors.html>`_
for a list of contributors to this library.

Contribute
----------

The fastest way to improve this project is to submit tested and documented
patches or detailed bug reports.

Donate
------

You can `donate via Liberapay`_.  This may speed up development or simply
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
