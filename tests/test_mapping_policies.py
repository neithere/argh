import sys
from argparse import ArgumentParser, Namespace
from typing import Callable, List

import pytest

from argh.assembling import NameMappingPolicy, infer_argspecs_from_function


@pytest.mark.parametrize("name_mapping_policy", list(NameMappingPolicy))
def test_no_args(name_mapping_policy) -> None:
    def func() -> None:
        ...

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, "usage: test [-h]\n")


@pytest.mark.parametrize("name_mapping_policy", list(NameMappingPolicy))
def test_one_positional(name_mapping_policy) -> None:
    def func(alpha: str) -> str:
        return f"{alpha}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, "usage: test [-h] alpha\n")
    assert_parsed(parser, ["hello"], Namespace(alpha="hello"))


@pytest.mark.parametrize("name_mapping_policy", list(NameMappingPolicy))
def test_two_positionals(name_mapping_policy) -> None:
    def func(alpha: str, beta: str) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, "usage: test [-h] alpha beta\n")
    assert_parsed(parser, ["one", "two"], Namespace(alpha="one", beta="two"))


@pytest.mark.parametrize(
    "name_mapping_policy,expected_usage",
    [
        (
            NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
            "usage: test [-h] [-b BETA] alpha\n",
        ),
        (NameMappingPolicy.BY_NAME_IF_KWONLY, "usage: test [-h] alpha [beta]\n"),
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


@pytest.mark.parametrize("name_mapping_policy", list(NameMappingPolicy))
def test_varargs(name_mapping_policy) -> None:
    def func(*file_paths) -> str:
        return f"{file_paths}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    expected_usage = "usage: test [-h] [file-paths ...]\n"
    if sys.version_info < (3, 9):
        # https://github.com/python/cpython/issues/82619
        expected_usage = "usage: test [-h] [file-paths [file-paths ...]]\n"
    assert_usage(parser, expected_usage)


@pytest.mark.parametrize(
    "name_mapping_policy,expected_usage",
    [
        (NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT, "usage: test [-h] alpha beta\n"),
        (NameMappingPolicy.BY_NAME_IF_KWONLY, "usage: test [-h] -b BETA alpha\n"),
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
            "usage: test [-h] [-a ALPHA] [-b BETA]\n",
        ),
        (NameMappingPolicy.BY_NAME_IF_KWONLY, "usage: test [-h] [-b BETA] [alpha]\n"),
    ],
)
def test_varargs_between_positional_and_kwonly__with_defaults(
    name_mapping_policy, expected_usage
) -> None:
    def func(alpha: int = 1, *, beta: int = 2) -> str:
        return f"{alpha}, {beta}"

    parser = _make_parser_for_function(func, name_mapping_policy=name_mapping_policy)
    assert_usage(parser, expected_usage)


def test_kwargs() -> None:
    def func(**kwargs) -> str:
        return f"{kwargs}"

    parser = _make_parser_for_function(
        func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_KWONLY
    )
    assert_usage(parser, "usage: test [-h]\n")


@pytest.mark.parametrize(
    "name_mapping_policy,expected_usage",
    [
        (
            NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
            "usage: test [-h] [-b BETA] [-d DELTA] alpha gamma\n",
        ),
        (
            NameMappingPolicy.BY_NAME_IF_KWONLY,
            "usage: test [-h] -g GAMMA [-d DELTA] alpha [beta]\n",
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
    name_mapping_policy: NameMappingPolicy = NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
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
    assert expected_usage == parser.format_usage()


def assert_parsed(
    parser: ArgumentParser, argv: List[str], expected_result: Namespace
) -> None:
    parsed = parser.parse_args(argv)
    assert parsed == expected_result
