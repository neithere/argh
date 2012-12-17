.. argh documentation master file, created by
   sphinx-quickstart on Tue Nov  9 23:06:31 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Agrh, argparse!
===============

Did you ever say "argh" trying to remember the details of `optparse` or
`argparse` API? If yes, this package may be useful for you.

`Argh` provides a very simple wrapper for `argparse`. `Argparse` is a very
powerful tool; `argh` just makes it easy to use.

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

Stability
---------

`Argh` is well-tested (could be better but still 80-100% test coverage).

The API may change in the future but there are no such plans yet.

Similar projects
----------------

* argdeclare_ requires additional classes and lacks support for nested
  commands.
* argparse-cli_ requires additional classes.
* django-boss_ seems to lack support for nested commands and is strictly
  Django-specific.
* entrypoint_ is lightweight but involves a lot of magic and seems to lack
  support for nested commands.
* opster_ and finaloption_ support nested commands but are based on the
  outdated `optparse` library and therefore reimplement some features available
  in `argparse`. They also introduce decorators that don't just decorate
  functions but change their behaviour, which is bad practice.
* simpleopt_ has an odd API and is rather a simple replacement for standard
  libraries than an extension.
* opterator_ is based on the outdated `optparse` and does not support nested
  commands.
* clap_ ships with its own parser and therefore is incompatible with
  `clap`-agnostic code.
* plac_ is a very powerful alternative to `argparse`. I'm not sure if it's
  worth migrating but it is surely very flexible and easy to use.

.. _argdeclare: http://code.activestate.com/recipes/576935-argdeclare-declarative-interface-to-argparse/
.. _argparse-cli: http://code.google.com/p/argparse-cli/
.. _django-boss: https://github.com/zacharyvoase/django-boss/tree/master/src/
.. _entrypoint: http://pypi.python.org/pypi/entrypoint/
.. _opster: http://pypi.python.org/pypi/opster/
.. _finaloption: http://pypi.python.org/pypi/finaloption/
.. _simpleopt: http://pypi.python.org/pypi/simpleopt/
.. _opterator: https://github.com/buchuki/opterator/
.. _clap: http://pypi.python.org/pypi/Clap/
.. _plac: http://micheles.googlecode.com/hg/plac/doc/plac.html

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
