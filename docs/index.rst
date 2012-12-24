Agrh, argparse!
===============

Did you ever say "argh" trying to remember the details of `optparse` or
`argparse` API? If yes, this package may be useful for you.

`Argh` provides a wrapper for `argparse`. `Argparse` is a very powerful tool;
`argh` just makes it easy to use.

In a nutshell
-------------

Here's a list of features that `argh` adds to `argparse`:

* mark a function as a CLI command and specify its arguments before the parser
  is instantiated;
* nested commands made easy: no messing with subparsers (though they are of
  course used under the hood);
* infer command name from function name;
* infer agrument type from the default value;
* infer argument action from the default value (for booleans);
* infer arguments from function signature;
* add an alias root command ``help`` for the ``--help`` argument;
* enable passing unwrapped arguments to certain functions instead of a
  :class:`argparse.Namespace` object.

`Argh` is fully compatible with `argparse`. You can mix `argh`-agnostic and
`argh`-aware code. Just keep in mind that :func:`~argh.dispatching.dispatch`
does some extra work that a custom dispatcher may not do.

Dependencies
------------

The `argh` library is supported (and tested unless otherwise specified) on
the following versions of Python:

* 2.6 (`argparse` library is required)
* 2.7 (including PyPy 1.8)
* 3.1 (`argparse` library is required; **not** tested)
* 3.2
* 3.3

.. versionchanged:: 0.15
   Added support for Python 3.x, dropped support for Python ≤ 2.5.

.. versionchanged:: 0.18
   Improved support for Python 3.2, added support for Python 3.3.

Details
-------

.. toctree::
   :maxdepth: 2

   tutorial
   reference
   similar

Stability
---------

`Argh` is well-tested (could be better but still 80-100% test coverage).

The API may change in the future but there are no such plans yet.

Why this one?
-------------

See :doc:`similar`.

Author
------

Developed by Andrey Mikhaylenko since 2010.

See :file:`AUTHORS` for a complete authors list of this application.

Please feel free to submit patches, report bugs or request features:

    http://bitbucket.org/neithere/argh/issues/

Glossary
--------

.. glossary::

    CLI
        `Command-line interface`_. You should know what that is if you are
        here, right? :)

    DRY
        The `don't repeat yourself`_ principle.

.. _Command-line interface: http://en.wikipedia.org/wiki/Command-line_interface
.. _Don't repeat yourself: http://en.wikipedia.org/wiki/Don't_repeat_yourself

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
