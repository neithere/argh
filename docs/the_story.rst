The Story of Argh
=================

Early history
-------------

Argh was first drafted by Andy in the airport while waiting for his flight.
The idea was to make a simplified wrapper for Argparse with support for nested
commands.  We'll focus on the function arguments vs. CLI arguments here.

This is what Argh began with (around 2010)::

    @arg("path", description="path to the file to load")
    @arg("--file-format", choices=["yaml", "json"], default="json")
    @arg("--dry-run", default=False)
    def load(args):
        do_something(args.path, args.file_format, args.dry_run)

    argh.dispatch_command(load)

You don't have to remember the details of the underlying Argparse interface
(especially for subparsers); you would still declare almost everything, but in
one place, close to the function itself.

"The Natural Way"
-----------------

In late 2012 the behaviour previously available via `@plain_signature`
decorator became standard::


    @arg("path", help="path to the file to load")
    @arg("--file-format", choices=["yaml", "json"])
    def load(path, file_format="json", dry_run=False):
        do_something(path, file_format, dry_run)

    argh.dispatch_command(load)

This unleashed the killer feature of Argh: now you can write normal functions —
not for argparse but general-purpose ones.  Argh would infer the basic CLI
argument definitions straight from the function signature.  The types and some
actions (e.g. `store_true`) would be inferred from defaults.  You would only need
to use the `@arg` decorator to enhance the information with something that had
no place in function signature of the Python 2.x era.

There's still an little ugly thing about it: you have to mention the argument
name twice, in function signature and the decorator.  Also the type cannot be
inferred if there's no default value, so you'd have to use the decorator even
for that.

Hiatus
------

The primary author's new job required focus on other languages for a number of
years and he had no energy to develop his FOSS projects, although he continued
using Argh for his own purposes on a daily basis.

A few forks were created by other developers but none survived.  (The forks,
not developers.)

By coincidence, around the beginning of this period a library called Click was
shipped with Flask and it seemed obvious that it will become the new standard
for simple CLI APIs and Argh wouldn't be needed. (Plot twist: it did become
popular but its goals are too different from Argh's to replace it.)

Revival
-------

The author returned to his FOSS projects in early 2023.  To his surprise, Argh
was not dead at all and its niche as the "natural API" was not occupied by any
other project.  It actually made sense to revive it.

A deep modernisation and refactoring began.

A number of pending issues were resolved and the last version to support
Python 2.x was released with a bunch of bugfixes.

The next few releases have deprecated and removed a lot of outdated features
and paved the way to a better Argh.  Some design decisions have been revised
and the streamlined.  The work continues.

Goodbye Decorators
------------------

As type hints became mature and widespread in Python code, the old approach
with decorators seems to make less and less sense.  A lot more can be now
inferred directly from the signature.  In fact, possibly everything.

Here's what Argh is heading for (around 2024).

A minimal example (note how there's literally nothing CLI-specific here)::

    def load(path: str, *, file_format: str = "json", dry_run: bool = False) -> str:
        return do_something(path, file_format, dry_run)

    argh.dispatch_command(load)

A more complete example::

    from typing import Annotated
    from argh import Help


    def load(
        path: Annotated[str, Help("path to the file to load")],
        *,
        file_format: Literal["json", "yaml"] = "json",
        dry_run: bool = False
    ) -> str:
        return do_something(path, file_format, dry_run)


    argh.dispatch_command(load)

The syntax is subject to change but the essence is clear:

* as few surprises to the reader as possible;
* the function used as a CLI command is declared and callable in the normal
  way, like any other function;
* type hints are used instead of ``@arg("foo", type=int)``
* additional metadata can be injected into type hints when necessary in a way
  that won't confuse type checkers (like in FastAPI_, requires Python 3.9+);
* non-kwonly become CLI positionals, kwonly become CLI options.

.. _FastAPI: https://fastapi.tiangolo.com/python-types/#type-hints-with-metadata-annotations
