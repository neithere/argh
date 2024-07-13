Changelog
=========

Version 0.31.3 (2024-07-13)
---------------------------

Bugs fixed:

- wrong type annotation of `errors` in `wrap_errors` (PR #229 by @laazy)
- tests were failing under Python 3.13 (issue #228 by @mgorny)
- regression: can't set argument name with `dest` via decorator
  (issue #224 by @mathieulongtin)

Version 0.31.2 (2024-01-24)
---------------------------

Bugs fixed:

- broken support for `Optional[List]` (but not `Optional[list]`), a narrower
  case of the problem fixed earlier (issue #216).

Version 0.31.1 (2024-01-19)
---------------------------

Bugs fixed:

- broken support for type alias `List` (issue #216).

Enhancements:

- cleaned up the README, rearranged other documentation.

Version 0.31.0 (2023-12-30)
---------------------------

Breaking changes:

- The typing hints introspection feature is automatically enabled for any
  command (function) which does **not** have any arguments specified via `@arg`
  decorator.

  This means that, for example, the following function used to fail and now
  it will pass::

      def main(count: int):
          assert isinstance(count, int)

  This may lead to unexpected behaviour in some rare cases.

- A small change in the legacy argument mapping policy `BY_NAME_IF_HAS_DEFAULT`
  concerning the order of variadic positional vs. keyword-only arguments.

  The following function now results in ``main alpha [args ...] beta`` instead of
  ``main alpha beta [args ...]``::

      def main(alpha, *args, beta): ...

  This does **not** concern the default name mapping policy.  Even for the
  legacy one it's an edge case which is extremely unlikely to appear in any
  real-life application.

- Removed the previously deprecated decorator `@expects_obj`.

Enhancements:

- Added experimental support for basic typing hints (issue #203)

  The following hints are currently supported:

  - ``str``, ``int``, ``float``, ``bool`` (goes to ``type``);
  - ``list`` (affects ``nargs``), ``list[T]`` (first subtype goes into ``type``);
  - ``Literal[T1, T2, ...]`` (interpreted as ``choices``);
  - ``Optional[T]`` AKA ``T | None`` (currently interpreted as
    ``required=False`` for optional and ``nargs="?"`` for positional
    arguments; likely to change in the future as use cases accumulate).

  The exact interpretation of the type hints is subject to change in the
  upcoming versions of Argh.

- Added `always_flush` argument to `dispatch()` (issue #145)

- High-level functions `argh.dispatch_command()` and `argh.dispatch_commands()`
  now accept a new parameter `old_name_mapping_policy`.  The behaviour hasn't
  changed because the parameter is `True` by default.  It will change to
  `False` in Argh v.0.33 or v.1.0.

Deprecated:

- the `namespace` argument in `argh.dispatch()` and `argh.parse_and_resolve()`.
  Rationale: continued API cleanup.  It's already possible to mutate the
  namespace object between parsing and calling the endpoint; it's unlikely that
  anyone would need to specify a custom namespace class or pre-populate it
  before parsing.  Please file an issue if you have a valid use case.

Other changes:

- Refactoring.

Version 0.30.5 (2023-12-25)
---------------------------

Bugs fixed:

- A combination of `nargs` with a list as default value would lead to the
  values coming from CLI being wrapped in another list (issue #212).

Enhancements:

- Argspec guessing: if `nargs` is not specified but the default value
  is a list, ``nargs="*"`` is assumed and passed to argparse.

Version 0.30.4 (2023-11-04)
---------------------------

There were complaints about the lack of a deprecation cycle for the legacy name
mapping policy.  This version addresses the issue:

- The handling introduced in v.0.30.2 (raising an exception for clarity)
  is retained for cases when no name mapping policy is specified but function
  signature contains defaults in non-kwonly args **and kwonly args are also
  defined**::

      def main(alpha, beta=1, *, gamma=2):  # error — explicit policy required

  In a similar case but when **kwonly args are not defined** Argh now assumes
  the legacy name mapping policy (`BY_NAME_IF_HAS_DEFAULT`) and merely issues
  a deprecation warning with the same message as the exception mentioned above::

      def main(alpha, beta=2):    # `[-b BETA] alpha` + DeprecationWarning

  This ensures that most of the old scripts still work the same way despite the
  new policy being used by default and enforced in cases when it's impossible
  to resolve the mapping conflict.

  Please note that this "soft" handling is to be removed in version v0.33
  (or v1.0 if the former is not deemed necessary).  The new name mapping policy
  will be used by default without warnings, like in v0.30.

Version 0.30.3 (2023-10-30)
---------------------------

Bugs fixed:

- Regression: a positional argument with an underscore used in `@arg` decorator
  would cause Argh fail on the assembling stage. (#208)

Version 0.30.2 (2023-10-24)
---------------------------

Bugs fixed:

- As reported in #204 and #206, the new default name mapping policy in fact
  silently changed the CLI API of some scripts: arguments which were previously
  translated as CLI options became optional positionals. Although the
  instructions were supplied in the release notes, the upgrade may not
  necessarily be intentional, so a waste of users' time is quite likely.

  To alleviate this, the default value for `name_mapping_policy` in standard
  functions has been changed to `None`; if it's not specified, Argh falls back
  to the new default policy, but raises `ArgumentNameMappingError` with
  detailed instructions if it sees a non-kwonly argument with a default value.

  Please specify the policy explicitly in order to avoid this error if you need
  to infer optional positionals (``nargs="?"``) from function signature.

Version 0.30.1 (2023-10-23)
---------------------------

Bugs fixed:

- Regression: certain special values in argument default value would cause an
  exception (#204)

Enhancements:

- Improved the tutorial.
- Added a more informative error message when the reason is likely to be
  related to the migration from Argh v0.29 to a version with a new argument
  name mapping policy.

Other changes:

- Added `py.typed` marker file for :pep:`561`.

Version 0.30.0 (2023-10-21)
---------------------------

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

Version 0.29.4 (2023-09-23)
---------------------------

Bugs fixed:

- Test coverage reported as <100% when argcomplete is installed (#187)

Versions 0.29.1 through 0.29.3
------------------------------

Technical releases for packaging purposes.  No changes in functionality.

Version 0.29.0 (2023-09-03)
---------------------------

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

Version 0.28.1 (2023-02-16)
---------------------------

- Fixed bugs in tests (#171, #172)

Version 0.28.0 (2023-02-15)
---------------------------

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

Version 0.27.2 (2023-02-09)
---------------------------

Minor packaging fix:

* chore: include file required by tox.ini in the sdist (#155)

Version 0.27.1 (2023-02-09)
---------------------------

Minor building and packaging fixes:

* docs: add Read the Docs config (#160)
* chore: include tox.ini in the sdist (#155)

Version 0.27.0 (2023-02-09)
---------------------------

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

Version 0.26.2 (2016-05-11)
---------------------------

- Removed official support for Python 3.4, added for 3.5.
- Various tox-related improvements for development.
- Improved documentation.

Version 0.26.1 (2014-10-30)
---------------------------

Fixed bugs:

- The undocumented (and untested) argument `dispatch(..., pre_call=x)`
  was broken; fixing because at least one important app depends on it
  (issue #63).

Version 0.26 (2014-10-27)
-------------------------

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

Version 0.25 (2014-07-05)
-------------------------

- Added EntryPoint class as another way to assemble functions (issue #59).

- Added support for Python 3.4; dropped support for Python 3.3
  (this doesn't mean that Argh is necessarily broken under 3.3,
  it's just that I'm not testing against it anymore).

- Shell completion warnings are now deprecated in favour of `logging`.

- The command help now displays default values of all arguments (issue #64).

- Function docstrings are now displayed verbatim in the help (issue #64).

- Argh's dispatching now should work properly in Cython.

Versions 0.2 through 0.24
-------------------------

A few years of development without a changelog 🫠

Fortunately, a curious reader can always refer to commit messages and
changesets.

Version 0.1 (2010-11-12)
------------------------

The first version!  A single file with 182 lines of code including
documentation :)  It featured subparsers and had the `@arg` decorator which was
basically a deferred `ArgumentParser.add_argument()` call.

Functions and classes:

* class `ArghParser`
* functions `add_commands()` and `dispatch()`
* decorators `@arg` and `@plain_signature`
