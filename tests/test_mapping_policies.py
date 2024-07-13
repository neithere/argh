import sys
from argparse import ArgumentParser, Namespace
from typing import Callable, List, Optional

import pytest

from argh.assembling import (
    ArgumentNameMappingError,
    NameMappingPolicy,
    infer_argspecs_from_function,
)

POLICIES = list(NameMappingPolicy) + [None]


@pytest.mark.parametrize("name_mapping_policy", POLICIES)
def test_no_args(name_mapping_policy) -> None:
    def func() -> None: ...

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, "usage: test [-h]")


@pytest.mark.parametrize("name_mapping_policy", POLICIES)
def test_one_positional(name_mapping_policy) -> None:
    def func(alpha: str) -> str:
        return f"{alpha}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, "usage: test [-h] alpha")
    assert_parsed(parser, ["hello"], Namespace(alpha="hello"))


@pytest.mark.parametrize("name_mapping_policy", POLICIES)
def test_two_positionals(name_mapping_policy) -> None:
    def func(alpha: str, beta: str) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, "usage: test [-h] alpha beta")
    assert_parsed(parser, ["one", "two"], Namespace(alpha="one", beta="two"))


@pytest.mark.parametrize(
    "name_mapping_policy,expected_usage",
    [
        (
            NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
            "usage: test [-h] [-b BETA] alpha",
        ),
        (NameMappingPolicy.BY_NAME_IF_KWONLY, "usage: test [-h] alpha [beta]"),
    ],
)
def test_two_positionals_one_with_default(name_mapping_policy, expected_usage) -> None:
    def func(alpha: str, beta: int = 123) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, expected_usage)

    assert_parsed(parser, ["one"], Namespace(alpha="one", beta=123))
    if name_mapping_policy == NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT:
        assert_parsed(
            parser, ["one", "--beta", "two"], Namespace(alpha="one", beta="two")
        )
    elif name_mapping_policy == NameMappingPolicy.BY_NAME_IF_KWONLY:
        assert_parsed(parser, ["one", "two"], Namespace(alpha="one", beta="two"))


@pytest.mark.parametrize("name_mapping_policy", POLICIES)
def test_varargs(name_mapping_policy) -> None:
    def func(*file_paths) -> str:
        return f"{file_paths}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    expected_usage = "usage: test [-h] [file-paths ...]"

    # TODO: remove once we drop support for Python 3.8
    if sys.version_info < (3, 9):
        # https://github.com/python/cpython/issues/82619
        expected_usage = "usage: test [-h] [file-paths [file-paths ...]]"

    assert_usage(parser, expected_usage)


@pytest.mark.parametrize(
    "name_mapping_policy,expected_usage",
    [
        (NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT, "usage: test [-h] alpha beta"),
        (NameMappingPolicy.BY_NAME_IF_KWONLY, "usage: test [-h] -b BETA alpha"),
        (None, "usage: test [-h] -b BETA alpha"),
    ],
)
def test_varargs_between_positional_and_kwonly__no_defaults(
    name_mapping_policy, expected_usage
) -> None:
    def func(alpha, *, beta) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, expected_usage)


@pytest.mark.parametrize(
    "name_mapping_policy,expected_usage",
    [
        (
            NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
            "usage: test [-h] [-a ALPHA] [-b BETA]",
        ),
        (NameMappingPolicy.BY_NAME_IF_KWONLY, "usage: test [-h] [-b BETA] [alpha]"),
    ],
)
def test_varargs_between_positional_and_kwonly__with_defaults(
    name_mapping_policy, expected_usage
) -> None:
    def func(alpha: int = 1, *, beta: int = 2) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, expected_usage)


def test_varargs_between_positional_and_kwonly__with_defaults__no_explicit_policy() -> (
    None
):
    def func(alpha: int = 1, *, beta: int = 2) -> str:
        return f"{alpha}, {beta}"

    with pytest.raises(ArgumentNameMappingError) as exc:
        _make_parser_for_function(func, name_mapping_policy=None)
    assert (
        'Argument "alpha" in function "func"\n'
        "is not keyword-only but has a default value."
    ) in str(exc.value)


# TODO: remove in v.0.33 if it happens, otherwise in v1.0.
def test_positional_with_defaults_without_kwonly__no_explicit_policy() -> None:
    def func(alpha: str, beta: int = 1) -> str:
        return f"{alpha} {beta}"

    message_pattern = 'Argument "beta" in function "func"\nis not keyword-only but has a default value.'
    with pytest.warns(DeprecationWarning, match=message_pattern):
        parser = _make_parser_for_function(func, name_mapping_policy=None)
    assert_usage(parser, "usage: test [-h] [-b BETA] alpha")


@pytest.mark.parametrize("name_mapping_policy", POLICIES)
def test_kwargs(name_mapping_policy) -> None:
    def func(**kwargs) -> str:
        return f"{kwargs}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, "usage: test [-h]")


@pytest.mark.parametrize(
    "name_mapping_policy,expected_usage",
    [
        (
            NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
            "usage: test [-h] [-b BETA] [-d DELTA] alpha gamma",
        ),
        (
            NameMappingPolicy.BY_NAME_IF_KWONLY,
            "usage: test [-h] -g GAMMA [-d DELTA] alpha [beta]",
        ),
    ],
)
def test_all_types_mixed_no_named_varargs(name_mapping_policy, expected_usage) -> None:
    def func(alpha: str, beta: int = 1, *, gamma: str, delta: int = 2) -> str:
        return f"{alpha}, {beta}, {gamma}, {delta}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, expected_usage)


def _make_parser_for_function(
    func: Callable,
    name_mapping_policy: Optional[NameMappingPolicy] = None,
) -> ArgumentParser:
    parser = ArgumentParser(prog="test")
    parser_add_argument_specs = infer_argspecs_from_function(
        function=func, name_mapping_policy=name_mapping_policy
    )
    for parser_add_argument_spec in parser_add_argument_specs:
        parser.add_argument(
            *parser_add_argument_spec.cli_arg_names,
            **parser_add_argument_spec.get_all_kwargs(),
        )
    return parser


def assert_usage(parser: ArgumentParser, expected_usage: str) -> None:
    if not expected_usage.endswith("\n"):
        expected_usage += "\n"
    assert expected_usage == parser.format_usage()


def assert_parsed(
    parser: ArgumentParser, argv: List[str], expected_result: Namespace
) -> None:
    parsed = parser.parse_args(argv)
    assert parsed == expected_result
