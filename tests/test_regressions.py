"""
Regression tests
~~~~~~~~~~~~~~~~
"""

import sys
from typing import List, Optional, TextIO

import pytest

import argh

from .base import DebugArghParser, run


def test_regression_issue12():
    """
    Issue #12: @command was broken if there were more than one argument
    to begin with same character (i.e. short option names were inferred
    incorrectly).
    """

    def cmd(*, foo=1, fox=2):
        yield f"foo {foo}, fox {fox}"

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "").out == "foo 1, fox 2\n"
    assert run(parser, "--foo 3").out == "foo 3, fox 2\n"
    assert run(parser, "--fox 3").out == "foo 1, fox 3\n"
    assert "unrecognized" in run(parser, "-f 3", exit=True)


def test_regression_issue12_help_flag():
    """
    Issue #12: if an argument starts with "h", e.g. "--host",
    ArgumentError is raised because "--help" is always added by argh
    without decorators.
    """

    def ddos(*, host="localhost"):
        return f"so be it, {host}!"

    # no help → no conflict
    parser = DebugArghParser("PROG", add_help=False)
    parser.set_default_command(ddos)
    assert run(parser, "-h 127.0.0.1").out == "so be it, 127.0.0.1!\n"

    # help added → conflict → short name ignored
    parser = DebugArghParser("PROG", add_help=True)
    parser.set_default_command(ddos)
    assert run(parser, "-h 127.0.0.1", exit=True) == 0


def test_regression_issue27():
    """
    Issue #27: store_true is not set for inferred bool argument.

    :Reason: when @command was refactored, it stopped using @arg, but it is
    it was there that guesses (choices→type, default→type and
    default→action) were made.
    """

    def parrot(*, dead=False):
        return "this parrot is no more" if dead else "beautiful plumage"

    def grenade(*, count=3):
        if count == 3:
            return "Three shall be the number thou shalt count"
        else:
            return "{0!r} is right out".format(count)

    parser = DebugArghParser()
    parser.add_commands([parrot, grenade])

    # default → type (int)
    assert run(parser, "grenade").out == (
        "Three shall be the number " "thou shalt count\n"
    )
    assert run(parser, "grenade --count 5").out == "5 is right out\n"

    # default → action (store_true)
    assert run(parser, "parrot").out == "beautiful plumage\n"
    assert run(parser, "parrot --dead").out == "this parrot is no more\n"


def test_regression_issue31():
    """
    Issue #31: Argh fails with parameter action type 'count' if a default
    value is provided.

    :Reason: assembling._guess() would infer type from default value without
        regard to the action.  _CountAction does not accept argument "type".

    :Solution: restricted type inferring to actions "store" and "append".
    """

    @argh.arg("-v", "--verbose", dest="verbose", action="count", default=0)
    def cmd(**kwargs):
        yield kwargs.get("verbose", -1)

    parser = DebugArghParser()
    parser.set_default_command(cmd)
    assert "0\n" == run(parser, "").out
    assert "1\n" == run(parser, "-v").out
    assert "2\n" == run(parser, "-vv").out


def test_regression_issue47():
    @argh.arg("--foo-bar", default="full")
    def func(foo_bar):
        return "hello"

    parser = DebugArghParser()
    with pytest.raises(argh.assembling.AssemblingError) as excinfo:
        parser.set_default_command(func)
    msg = (
        'func: argument "foo_bar" declared as positional (in function '
        "signature) and optional (via decorator). If you've just migrated "
        "from Argh v.0.29, please check the new default NameMappingPolicy. "
        "Perhaps you need to replace `func(x=1)` with `func(*, x=1)`?"
    )
    assert excinfo.exconly().endswith(msg)


def test_regression_issue76():
    """
    Issue #76: optional arguments defaulting to the empty string break --help.

    This is also tested in integration tests but in a different way.
    """

    def cmd(*, foo=""):
        pass

    parser = DebugArghParser()
    parser.set_default_command(cmd)
    run(parser, "--help", exit=True)


def test_regression_issue104():
    """
    Issue #76: Bug in the way **kwargs is handled

    **kwargs handling was broken in the case that required (no default
    value) positional argument names contained underscores.
    """

    def cmd(foo_foo, bar_bar, *, baz_baz=5, bip_bip=9, **kwargs):
        return "\n".join(
            [str(foo_foo), str(bar_bar), str(baz_baz), str(bip_bip), str(kwargs)]
        )

    parser = DebugArghParser()
    parser.set_default_command(cmd)
    expected = "abc\ndef\n8\n9\n{}\n"
    assert run(parser, "abc def --baz-baz 8").out == expected


def test_regression_issue204():
    """
    Issue #204: `asdict(ParserAddArgumentSpec)` used `deepcopy` which would
    lead to "TypeError: cannot pickle..." if e.g. a default value contained an
    un-pickle-able object.

    We should avoid `deepcopy()` in standard operations.
    """

    def func(*, x: TextIO = sys.stdout) -> None: ...

    parser = DebugArghParser()
    parser.set_default_command(func)


def test_regression_issue208():
    @argh.arg("foo_bar", help="fooooo")
    def func(foo_bar):
        return foo_bar

    parser = DebugArghParser()
    parser.set_default_command(func)


def test_regression_issue212_orig_use_case():
    """
    Issue #212: a combination of nargs with list as default value would result
    in a nested list instead of a flat list.

    Variation: original use case (default value via decorator).
    """

    @argh.arg("paths", nargs="*", default=["one", "two"])
    def func(paths: List[str]):
        return f"{paths}"

    parser = DebugArghParser()
    parser.set_default_command(func)

    assert run(parser, "").out == "['one', 'two']\n"
    assert run(parser, "alpha").out == "['alpha']\n"
    assert run(parser, "alpha beta gamma").out == "['alpha', 'beta', 'gamma']\n"


def test_regression_issue212_funcsig_centric_positional():
    """
    Issue #212: a combination of nargs with list as default value would result
    in a nested list instead of a flat list.

    Variation: default value via function signature (positional).
    """

    @argh.arg("paths", nargs="*")
    def func(paths: Optional[List[str]] = ["one", "two"]):
        return f"{paths}"

    parser = DebugArghParser()
    parser.set_default_command(
        func, name_mapping_policy=argh.assembling.NameMappingPolicy.BY_NAME_IF_KWONLY
    )

    assert run(parser, "").out == "['one', 'two']\n"
    assert run(parser, "alpha").out == "['alpha']\n"
    assert run(parser, "alpha beta gamma").out == "['alpha', 'beta', 'gamma']\n"


def test_regression_issue212_funcsig_centric_named():
    """
    Issue #212: a combination of nargs with list as default value would result
    in a nested list instead of a flat list.

    Variation: default value via function signature (named).
    """

    @argh.arg("--paths", nargs="*")
    def func(*, paths: Optional[List[str]] = ["one", "two"]):
        return f"{paths}"

    parser = DebugArghParser()
    parser.set_default_command(func)

    assert run(parser, "").out == "['one', 'two']\n"
    assert run(parser, "--paths alpha").out == "['alpha']\n"
    assert run(parser, "--paths alpha beta gamma").out == "['alpha', 'beta', 'gamma']\n"


def test_regression_issue224():
    """
    Issue #224: @arg param `dest` was ignored and Argh was unable to map the
    declaration onto the function signature.

    Use case: expose a function argument with a different name in the CLI.
    """

    @argh.arg("-l", dest="list_files")
    def func(*, list_files=False):
        return f"list_files={list_files}"

    parser = DebugArghParser()
    parser.set_default_command(func)

    assert run(parser, "").out == "list_files=False\n"
    assert run(parser, "-l").out == "list_files=True\n"
