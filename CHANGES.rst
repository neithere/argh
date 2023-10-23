~~~~~~~~~
Changelog
~~~~~~~~~

Version 0.30.1
--------------

Bugs fixed:

- Regression: certain special values in argument default value would cause an
  exception (#204)

Enhancements:

- Improved the tutorial.

Other changes:

- Added `py.typed` marker file for :pep:`561`.

Version 0.30.0
--------------

Backwards incompatible changes:

- A new policy for mapping function arguments to CLI arguments is used by
  default (see :class:`argh.assembling.NameMappingPolicy`).

  The following function does **not** map to ``func foo [--bar]`` anymore::

      def func(foo, bar=None):
          ...

  Since this release it maps to ``func foo [bar]`` instead.
  Please update the function this way to keep `bar` an "option"::

      def func(foo, *, bar=None):
          ...

  If you cannot modify the function signature to use kwonly args for options,
  please consider explicitly specifying the legacy name mapping policy::

      set_default_command(
          func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT
      )

- The name mapping policy `BY_NAME_IF_HAS_DEFAULT` slightly deviates from the
  old behaviour. Kwonly arguments without default values used to be marked as
  required options (``--foo FOO``), now they are treated as positionals
  (``foo``). Please consider the new default policy (`BY_NAME_IF_KWONLY`) for
  a better treatment of kwonly.

- Removed previously deprecated features (#184 → #188):

  - argument help string in annotations — reserved for type hints;
  - `argh.SUPPORTS_ALIASES`;
  - `argh.safe_input()`;
  - previously renamed arguments for `add_commands()`: `namespace`,
    `namespace_kwargs`, `title`, `description`, `help`;
  - `pre_call` argument in `dispatch()`.  The basic usage remains simple but
    more granular functions are now available for more control.

    Instead of this::

      argh.dispatch(..., pre_call=pre_call_hook)

    please use this::

      func, ns = argh.parse_and_resolve(...)
      pre_call_hook(ns)
      argh.run_endpoint_function(func, ns, ...)

Deprecated:

- The `@expects_obj` decorator.  Rationale: it used to support the old,
  "un-pythonic" style of usage, which essentially lies outside the scope of
  Argh.  If you are not using the mapping of function arguments onto CLI, then
  you aren't reducing the amount of code compared to vanilla Argparse.

- The `add_help_command` argument in `dispatch()`.
  Rationale: it doesn't add much to user experience; it's not much harder to
  type ``--help`` than it is to type ``help``; moreover, the option can be
  added anywhere, unlike its positional counterpart.

Enhancements:

- Added support for Python 3.12.
- Added type annotations to existing Argh code (#185 → #189).
- The `dispatch()` function has been refactored, so in case you need finer
  control over the process, two new, more granular functions can be used:

  - `endpoint_function, namespace = argh.parse_and_resolve(...)`
  - `argh.run_endpoint_function(endpoint_function, namespace, ...)`

  Please note that the names may change in the upcoming versions.

- Configurable name mapping policy has been introduced for function argument
  to CLI argument translation (#191 → #199):

  - `BY_NAME_IF_KWONLY` (default and recommended).
  - `BY_NAME_IF_HAS_DEFAULT` (close to pre-v.0.30 behaviour);

  Please check API docs on :class:`argh.assembling.NameMappingPolicy` for
  details.

Version 0.29.4
--------------

Bugs fixed:

- Test coverage reported as <100% when argcomplete is installed (#187)

Versions 0.29.1 through 0.29.3
------------------------------

Technical releases for packaging purposes.  No changes in functionality.

Version 0.29.0
--------------

Backwards incompatible changes:

- Wrapped exceptions now cause ``dispatching.dispatch()`` to raise
  ``SystemExit(1)`` instead of returning without error. For most users, this
  means failed commands will now exit with a failure status instead of a
  success. (#161)

Deprecated:

- Renamed arguments in `add_commands()` (#165):

  - `namespace` → `group_name`
  - `namespace_kwargs` → `group_kwargs`

  The old names are deprecated and will be removed in v.0.30.

Enhancements:

- Can control exit status (see Backwards Incompatible Changes above) when
  raising ``CommandError`` using the ``code`` keyword arg.

Bugs fixed:

-  Positional arguments should not lead to removal of short form of keyword
   arguments. (#115)

Other changes:

- Avoid depending on iocapture by using pytest's built-in feature (#177)

Version 0.28.1
--------------

- Fixed bugs in tests (#171, #172)

Version 0.28.0
--------------

A major cleanup.

Backward incompatible changes:

- Dropped support for Python 2.7 and 3.7.

Deprecated features, to be removed in v.0.30:

- `argh.assembling.SUPPORTS_ALIASES`.

  - Always `True` for recent versions of Python.

- `argh.io.safe_input()` AKA `argh.interaction.safe_input()`.

  - Not relevant anymore.  Please use the built-in `input()` instead.

- argument `pre_call` in `dispatch()`.

   Even though this hack seems to have been used in some projects, it was never
   part of the official API and never recommended.

   Describing your use case in the `discussion about shared arguments`_ can
   help improve the library to accomodate it in a proper way.

   .. _discussion about shared arguments: https://github.com/neithere/argh/issues/63

- Argument help as annotations.

  - Annotations will only be used for types after v.0.30.
  - Please replace any instance of::

      def func(foo: "Foobar"):

    with the following::

      @arg('-f', '--foo', help="Foobar")
      def func(foo):

    It will be decided later how to keep this functionality "DRY" (don't repeat
    yourself) without conflicts with modern conventions and tools.

- Added deprecation warnings for some arguments deprecated back in v.0.26.

Version 0.27.2
--------------

Minor packaging fix:

* chore: include file required by tox.ini in the sdist (#155)

Version 0.27.1
--------------

Minor building and packaging fixes:

* docs: add Read the Docs config (#160)
* chore: include tox.ini in the sdist (#155)

Version 0.27.0
--------------

This is the last version to support Python 2.7.

Backward incompatible changes:

- Dropped support for Python 2.6.

Enhancements:

- Added support for Python 3.7 through 3.11.
- Support introspection of function signature behind the `@wraps` decorator
  (issue #111).

Fixed bugs:

- When command function signature contained ``**kwargs`` *and* positionals
  without defaults and with underscores in their names, a weird behaviour could
  be observed (issue #104).
- Fixed introspection through decorators (issue #111).
- Switched to Python's built-in `unittest.mock` (PR #154).
- Fixed bug with `skip_unknown_args=True` (PR #134).
- Fixed tests for Python 3.9.7+ (issue #148).

Other changes:

- Included the license files in manifest (PR #112).
- Extended the list of similar projects (PR #87).
- Fixed typos and links in documentation (PR #110, #116, #156).
- Switched CI to Github Actions (PR #153).

Version 0.26.2
--------------

- Removed official support for Python 3.4, added for 3.5.
- Various tox-related improvements for development.
- Improved documentation.

Version 0.26.1
--------------

Fixed bugs:

- The undocumented (and untested) argument `dispatch(..., pre_call=x)`
  was broken; fixing because at least one important app depends on it
  (issue #63).

Version 0.26
------------

This release is intended to be the last one before 1.0.  Therefore a major
cleanup was done.  This **breaks backward compatibility**.  If your code is
really outdated, please read this list carefully and grep your code.

- Removed decorator `@alias` (deprecated since v.0.19).

- Removed decorator `@plain_signature` (deprecated since v.0.20).

- Dropped support for old-style functions that implicitly expected namespace
  objects (deprecated since v.0.21).  The `@expects_obj` decorator is now
  mandatory for such functions.

- Removed decorator `@command` (deprecated since v.0.21).

- The `@wrap_errors` decorator now strictly requires that the error classes
  are given as a list (old behaviour was deprecated since v.0.22).

- The `allow_warnings` argument is removed from
  `argh.completion.autocomplete()`.  Debug-level logging is used instead.
  (The warnings were deprecated since v.0.25).

Deprecated:

- Deprecated arguments `title`, `help` and `description` in `add_commands()`
  helper function.  See documentation and issue #60.

Other changes:

- Improved representation of default values in the help.

- Dispatcher can be configured to skip unknown arguments (issue #57).

- Added `add_subcommands()` helper function (a convenience wrapper
  for `add_commands()`).

- `EntryPoint` now stores kwargs for the parser.

- Added support for default command *with* nested commands (issue #78).

  This only works with Python 3.4+ due to incorrect behaviour or earlier
  versions of Argparse (including the stand-alone one as of 1.2.1).

  Due to argparse peculiarities the function assignment technique relies
  on a special `ArghNamespace` object.  It is used by default in `ArghParser`
  and the shortcuts, but if you call the vanilla `ArgumentParser.parse_args()`
  method, you now *have* to supply the proper namespace object.

Fixed bugs:

- Help formatter was broken for arguments with empty strings as default values
  (issue #76).

Version 0.25
------------

- Added EntryPoint class as another way to assemble functions (issue #59).

- Added support for Python 3.4; dropped support for Python 3.3
  (this doesn't mean that Argh is necessarily broken under 3.3,
  it's just that I'm not testing against it anymore).

- Shell completion warnings are now deprecated in favour of `logging`.

- The command help now displays default values of all arguments (issue #64).

- Function docstrings are now displayed verbatim in the help (issue #64).

- Argh's dispatching now should work properly in Cython.
