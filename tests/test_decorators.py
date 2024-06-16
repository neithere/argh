"""
Unit Tests For Decorators
~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import pytest

import argh
from argh.dto import ParserAddArgumentSpec
from argh.utils import (
    CliArgToFuncArgGuessingError,
    MixedPositionalAndOptionalArgsError,
    TooManyPositionalArgumentNames,
    naive_guess_func_arg_name,
)


def test_aliases():
    @argh.aliases("one", "two")
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_ALIASES)
    assert attr == ("one", "two")


def test_arg():
    @argh.arg("foo", help="my help", nargs="+")
    @argh.arg("--bar", default=1)
    def func():
        pass

    attrs = getattr(func, argh.constants.ATTR_ARGS)
    assert attrs == [
        ParserAddArgumentSpec(
            func_arg_name="foo",
            cli_arg_names=["foo"],
            nargs="+",
            other_add_parser_kwargs={
                "help": "my help",
            },
        ),
        ParserAddArgumentSpec(
            func_arg_name="bar",
            cli_arg_names=["--bar"],
            default_value=1,
        ),
    ]


def test_named():
    @argh.named("new-name")
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_NAME)
    assert attr == "new-name"


def test_wrap_errors():
    @argh.wrap_errors([KeyError, ValueError])
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_WRAPPED_EXCEPTIONS)
    assert attr == [KeyError, ValueError]


def test_wrap_errors_processor():
    @argh.wrap_errors(processor="STUB")
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_WRAPPED_EXCEPTIONS_PROCESSOR)
    assert attr == "STUB"


def test_naive_guess_func_arg_name() -> None:
    # none (error)
    with pytest.raises(CliArgToFuncArgGuessingError):
        argh.arg()(lambda foo: foo)

    # positional
    assert naive_guess_func_arg_name(("foo",)) == "foo"

    # positional — more than one (error)
    with pytest.raises(TooManyPositionalArgumentNames):
        argh.arg("foo", "bar")(lambda foo: foo)

    # option
    assert naive_guess_func_arg_name(("-x",)) == "x"
    assert naive_guess_func_arg_name(("--foo",)) == "foo"
    assert naive_guess_func_arg_name(("--foo", "-f")) == "foo"
    assert naive_guess_func_arg_name(("-f", "--foo")) == "foo"
    assert naive_guess_func_arg_name(("-x", "--foo", "--bar")) == "foo"

    with pytest.raises(CliArgToFuncArgGuessingError):
        naive_guess_func_arg_name(("-x", "-y"))

    # mixed (errors)
    with pytest.raises(MixedPositionalAndOptionalArgsError):
        argh.arg("foo", "--foo")(lambda foo: foo)

    with pytest.raises(MixedPositionalAndOptionalArgsError):
        argh.arg("--foo", "foo")(lambda foo: foo)

    with pytest.raises(MixedPositionalAndOptionalArgsError):
        argh.arg("-f", "foo")(lambda foo: foo)

    with pytest.raises(MixedPositionalAndOptionalArgsError):
        argh.arg("foo", "-f")(lambda foo: foo)
