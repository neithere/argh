Similar projects
~~~~~~~~~~~~~~~~

Obviously, `Argh` is not the only CLI helper library in the Python world.
It was created when some similar solutions already existed; more appeared
later on.  There are valid reasons behind maintaining most projects.

The list below is nowhere near exhausting; certain items are yet to be
reviewed; the comments should have been more structured.  However, it gives
a picture of the alternatives.

Ideally, we'd need a table with the following columns: supports argparse;
has integrated parser; requires subclassing; supports nested commands;
is bound to an unrelated piece of software; involves "magic" (i.e. undermines
clarity); depends on outdated libraries; has simple API; has unobtrusive API;
supports Python3.  Not every "yes" in this table would count as pro.

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
* baker_
* plumbum_
* docopt_
* aaargh_
* cliff_
* cement_
* autocommand_

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
.. _baker: http://pypi.python.org/pypi/Baker/
.. _plumbum: http://plumbum.readthedocs.org/en/latest/cli.html
.. _docopt: http://docopt.org
.. _aaargh: http://pypi.python.org/pypi/aaargh
.. _cliff: http://pypi.python.org/pypi/cliff
.. _cement: http://builtoncement.com/2.0/
.. _autocommand: https://pypi.python.org/pypi/autocommand/
