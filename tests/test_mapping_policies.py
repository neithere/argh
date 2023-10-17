from argparse import ArgumentParser, Namespace
from typing import Callable
import pytest

from argh.assembling import DefaultsPolicies, infer_argspecs_from_function


@pytest.mark.parametrize("defaults_policy", list(DefaultsPolicies))
def test_no_args(defaults_policy) -> None:
    def func() -> None:
        ...

    parser = _make_parser_for_function(func, defaults_policy=defaults_policy)
    assert_usage(parser, "usage: test [-h]\n")


@pytest.mark.parametrize("defaults_policy", list(DefaultsPolicies))
def test_one_positional(defaults_policy) -> None:
    def func(alpha: str) -> str:
        return f"{alpha}"

    parser = _make_parser_for_function(func, defaults_policy=defaults_policy)
    assert_usage(parser, "usage: test [-h] alpha\n")
    assert_parsed(parser, ["hello"], Namespace(alpha="hello"))


@pytest.mark.parametrize("defaults_policy", list(DefaultsPolicies))
def test_two_positionals(defaults_policy) -> None:
    def func(alpha: str, beta: str) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, defaults_policy=defaults_policy)
    assert_usage(parser, "usage: test [-h] alpha beta\n")
    assert_parsed(parser, ["one", "two"], Namespace(alpha="one", beta="two"))


@pytest.mark.parametrize("defaults_policy,expected_usage", [
    (DefaultsPolicies.BASIC, "usage: test [-h] [-b BETA] alpha\n"),
    (DefaultsPolicies.KWONLY, "usage: test [-h] alpha [beta]\n"),
])
def test_two_positionals_one_with_default(defaults_policy, expected_usage) -> None:
    def func(alpha: str, beta: int = 123) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, defaults_policy=defaults_policy)
    assert_usage(parser, expected_usage)

    assert_parsed(parser, ["one"], Namespace(alpha="one", beta=123))
    if defaults_policy == DefaultsPolicies.BASIC:
        assert_parsed(parser, ["one", "--beta", "two"], Namespace(alpha="one", beta="two"))
    elif defaults_policy == DefaultsPolicies.KWONLY:
        assert_parsed(parser, ["one", "two"], Namespace(alpha="one", beta="two"))


@pytest.mark.parametrize("defaults_policy", list(DefaultsPolicies))
def test_varargs(defaults_policy) -> None:

    def func(*file_paths) -> str:
        return f"{file_paths}"

    parser = _make_parser_for_function(func, defaults_policy=defaults_policy)
    assert_usage(parser, "usage: test [-h] [file_paths ...]\n")


@pytest.mark.parametrize("defaults_policy,expected_usage", [
    (DefaultsPolicies.BASIC, "usage: test [-h] -b BETA alpha\n"),
    (DefaultsPolicies.KWONLY, "usage: test [-h] -b BETA alpha\n"),
])
def test_varargs_between_positional_and_kwonly__no_defaults(defaults_policy, expected_usage) -> None:

    def func(alpha, *, beta) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, defaults_policy=defaults_policy)
    assert_usage(parser, expected_usage)


@pytest.mark.parametrize("defaults_policy,expected_usage", [
    (DefaultsPolicies.BASIC, "usage: test [-h] [-a ALPHA] [-b BETA]\n"),
    (DefaultsPolicies.KWONLY, "usage: test [-h] [-b BETA] [alpha]\n"),
])
def test_varargs_between_positional_and_kwonly__with_defaults(defaults_policy, expected_usage) -> None:

    def func(alpha: int = 1, *, beta: int = 2) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, defaults_policy=defaults_policy)
    assert_usage(parser, expected_usage)


def test_kwargs() -> None:

    def func(**kwargs) -> str:
        return f"{kwargs}"

    parser = _make_parser_for_function(func, defaults_policy=DefaultsPolicies.KWONLY)
    assert_usage(parser, "usage: test [-h]\n")


@pytest.mark.parametrize("defaults_policy,expected_usage", [
    (DefaultsPolicies.BASIC, "usage: test [-h] [-b BETA] -g GAMMA [-d DELTA] alpha\n"),
    (DefaultsPolicies.KWONLY, "usage: test [-h] -g GAMMA [-d DELTA] alpha [beta]\n"),
])
def test_all_types_mixed_no_named_varargs(defaults_policy, expected_usage) -> None:

    def func(alpha: str, beta: int = 1, *, gamma: str, delta: int = 2) -> str:
        return f"{alpha}, {beta}, {gamma}, {delta}"

    parser = _make_parser_for_function(func, defaults_policy=defaults_policy)
    assert_usage(parser, expected_usage)


def _make_parser_for_function(
    func: Callable, defaults_policy: str = DefaultsPolicies.BASIC
) -> ArgumentParser:
    parser = ArgumentParser(prog="test")
    parser_add_argument_specs = infer_argspecs_from_function(
        function=func, defaults_policy=defaults_policy
    )
    for parser_add_argument_spec in parser_add_argument_specs:
        parser.add_argument(
            *parser_add_argument_spec.cli_arg_names,
            **parser_add_argument_spec.get_all_kwargs()
        )
    return parser


def assert_usage(parser: ArgumentParser, expected_usage: str) -> None:
    assert expected_usage == parser.format_usage()

def assert_parsed(parser: ArgumentParser, argv: list[str], expected_result: Namespace) -> None:
    parsed = parser.parse_args(argv)
    assert parsed == expected_result
