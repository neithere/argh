Subparsers
==========

The statement ``parser.add_commands([bar, quux])`` builds two subparsers named
`bar` and `quux`. A "subparser" is an argument parser bound to a group name. In
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

    foo_parser = subparsers.add_parser("foo")
    foo_parser.set_defaults(function=foo)

    bar_parser = subparsers.add_parser("bar")
    bar_parser.set_defaults(function=bar)

    args = parser.parse_args()
    print(args.function(args))

Now consider this expression::

    parser = ArghParser()
    parser.add_commands([bar, quux], group_name="foo")
    parser.dispatch()

It produces a command hierarchy for the command-line expressions ``foo bar``
and ``foo quux``. This involves "subsubparsers". Without `Argh` you would need
to write something like this (generic argparse API)::

    import sys
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    foo_parser = subparsers.add_parser("foo")
    foo_subparsers = foo_parser.add_subparsers()

    foo_bar_parser = foo_subparsers.add_parser("bar")
    foo_bar_parser.set_defaults(function=bar)

    foo_quux_parser = foo_subparsers.add_parser("quux")
    foo_quux_parser.set_defaults(function=quux)

    args = parser.parse_args()
    print(args.function(args))

.. note::

    You don't have to use :class:`~argh.helpers.ArghParser`; the standard
    :class:`argparse.ArgumentParser` will do. You will just need to call
    stand-alone functions :func:`argh.assembling.add_commands` and
    :func:`argh.dispatching.dispatch` instead of
    :class:`argh.helpers.ArghParser` methods.
