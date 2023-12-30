Cookbook
========

Multiple values per argument
----------------------------

Use `nargs` from argparse by amending the function signature with the
:func:`argh.decorators.arg` decorator:

.. code-block:: python

    @argh.arg("-p", "--patterns", nargs="*")
    def cmd(*, patterns: list[str] | None = None) -> list:
        distros = ("abc", "xyz")
        return [
            d for d in distros if not patterns or any(p in d for p in patterns)
        ]

Resulting CLI::

  $ app
  abc
  xyz

  $ app --patterns
  abc
  xyz

  $ app -p a
  abc

  $ app -p ab yz
  abc
  xyz

Note that you need to specify both short and long names of the argument because
`@arg` turns off the "smart" mechanism.

In fact, you don't even need to use `nargs` if you specify a list as the
default value (and provided that you're using the name mapping policy which
will be eventually the default one):

.. code-block:: python

    def cmd(patterns: list[str] = ["default-pattern"]) -> list:
        distros = ("abc", "xyz")
        return [d for d in distros if any(p in d for p in patterns)]

    argh.dispatch_command(cmd, old_name_mapping_policy=False)
