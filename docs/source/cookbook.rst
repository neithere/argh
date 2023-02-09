Cookbook
~~~~~~~~

Multiple values per argument
----------------------------

Use `nargs` from argparse by amending the function signature with the
:func:`argh.decorators.arg` decorator:

.. code-block:: python

    @argh.arg('-p', '--patterns', nargs='*')
    def cmd(patterns=None):
        distros = ('abc', 'xyz')
        return [d for d in distros if not patterns
                                      or any(p in d for p in patterns)]

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
