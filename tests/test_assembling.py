"""
Unit Tests For Assembling Phase
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import argparse
from typing import Literal, Optional
from unittest.mock import MagicMock, call, patch

import pytest

import argh
from argh.assembling import AssemblingError, NameMappingPolicy
from argh.dto import ParserAddArgumentSpec


def test_guess_type_from_choices():
    given = ParserAddArgumentSpec(
        "foo", ["foo"], other_add_parser_kwargs={"choices": [1, 2]}
    )
    guessed = {"type": int}
    assert guessed == argh.assembling.guess_extra_parser_add_argument_spec_kwargs(given)

    # do not override a guessable param if already explicitly defined
    given = ParserAddArgumentSpec(
        "foo",
        ["foo"],
        other_add_parser_kwargs={
            "option_strings": ["foo"],
            "choices": [1, 2],
            "type": "NO_MATTER_WHAT",
        },
    )
    guessed = {}
    assert guessed == argh.assembling.guess_extra_parser_add_argument_spec_kwargs(given)


def test_guess_type_from_default():
    given = ParserAddArgumentSpec("foo", ["foo"], default_value=1)
    guessed = {"type": int}
    assert guessed == argh.assembling.guess_extra_parser_add_argument_spec_kwargs(given)

    # do not override a guessable param if already explicitly defined
    given = ParserAddArgumentSpec(
        "foo",
        ["foo"],
        default_value=1,
        other_add_parser_kwargs={
            "type": "NO_MATTER_WHAT",
        },
    )
    guessed = {}
    assert guessed == argh.assembling.guess_extra_parser_add_argument_spec_kwargs(given)


def test_guess_action_from_default():
    # positional, default True → ignore
    given = ParserAddArgumentSpec("foo", ["foo"], default_value=False)
    assert {} == argh.assembling.guess_extra_parser_add_argument_spec_kwargs(given)

    # named, default True → store_false
    given = ParserAddArgumentSpec("foo", ["--foo"], default_value=False)
    guessed = {"action": "store_true"}
    assert guessed == argh.assembling.guess_extra_parser_add_argument_spec_kwargs(given)

    # positional, default False → ignore
    given = ParserAddArgumentSpec("foo", ["foo"], default_value=True)
    assert {} == argh.assembling.guess_extra_parser_add_argument_spec_kwargs(given)

    # named, True → store_false
    given = ParserAddArgumentSpec("foo", ["--foo"], default_value=True)
    guessed = {"action": "store_false"}
    assert guessed == argh.assembling.guess_extra_parser_add_argument_spec_kwargs(given)

    # do not override a guessable param if already explicitly defined
    given = ParserAddArgumentSpec(
        "foo",
        ["foo"],
        default_value=False,
        other_add_parser_kwargs={
            "action": "NO_MATTER_WHAT",
        },
    )
    guessed = {}
    assert guessed == argh.assembling.guess_extra_parser_add_argument_spec_kwargs(given)


def test_positional_with_default_int():
    def func(pos_int_default=123): ...

    parser = argh.ArghParser(prog="test")
    parser.set_default_command(
        func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_KWONLY
    )
    assert parser.format_usage() == "usage: test [-h] [pos-int-default]\n"
    assert "pos-int-default  123" in parser.format_help()


def test_positional_with_default_bool():
    def func(pos_bool_default=False): ...

    parser = argh.ArghParser(prog="test")
    parser.set_default_command(
        func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_KWONLY
    )
    assert parser.format_usage() == "usage: test [-h] [pos-bool-default]\n"
    assert "pos-bool-default  False" in parser.format_help()


def test_set_default_command():
    def func(**kwargs):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        [
            ParserAddArgumentSpec(
                func_arg_name="foo",
                cli_arg_names=("foo",),
                nargs=argparse.ONE_OR_MORE,
                other_add_parser_kwargs={"choices": [1, 2], "help": "me"},
            ),
            ParserAddArgumentSpec(
                func_arg_name="bar", cli_arg_names=("-b", "--bar"), default_value=False
            ),
        ],
    )

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        call("foo", nargs=argparse.ONE_OR_MORE, choices=[1, 2], help="me", type=int),
        call(
            "-b",
            "--bar",
            default=False,
            action="store_true",
            help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE,
        ),
    ]
    assert parser.set_defaults.mock_calls == [call(function=func)]


def test_set_default_command__parser_error():
    def func(foo: str) -> str:
        return foo

    parser_mock = MagicMock(spec=argparse.ArgumentParser)
    parser_mock.add_help = False
    parser_mock.add_argument.side_effect = argparse.ArgumentError(
        None, "my hat's on fire!"
    )

    with pytest.raises(argh.AssemblingError):
        argh.set_default_command(parser_mock, func)


def test_set_default_command__no_func_args():
    # TODO: document in changelog
    # XXX breaking change in v0.30!
    #     Old behaviour: @arg declarations would be passed to add_argument().
    #                    (how the hell would it look like though?)
    #     New behaviour: @arg declarations are ignored because there's no func
    #                    arg to map them onto.
    def func():
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        [ParserAddArgumentSpec(func_arg_name="x", cli_arg_names=("-x",))],
    )

    p = argh.ArghParser()

    with pytest.raises(argh.AssemblingError) as excinfo:
        p.set_default_command(func)
    msg = (
        "func: cannot extend argument declarations for an endpoint "
        "function that takes no arguments."
    )
    assert msg in str(excinfo.value)


def test_set_default_command__varargs_vs_positional():
    def func(*args):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        [ParserAddArgumentSpec(func_arg_name="x", cli_arg_names=("x",))],
    )

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    with pytest.raises(
        AssemblingError, match="func: argument x does not fit function signature: args"
    ):
        parser.set_default_command(func)


def test_set_default_command__varargs_vs_optional():
    def func(*args):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        [ParserAddArgumentSpec(func_arg_name="x", cli_arg_names=("-x",))],
    )

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    with pytest.raises(
        AssemblingError, match="func: argument -x does not fit function signature: args"
    ):
        parser.set_default_command(func)


def test_set_default_command__varkwargs_vs_positional():
    def func(**kwargs):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        [ParserAddArgumentSpec(func_arg_name="x", cli_arg_names=("x",))],
    )

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    parser.set_default_command(func)
    assert parser.add_argument.mock_calls == [call("x", help="%(default)s")]
    assert parser.set_defaults.mock_calls == [call(function=func)]


def test_set_default_command__varkwargs_vs_optional():
    def func(**kwargs):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        [ParserAddArgumentSpec(func_arg_name="x", cli_arg_names=("-x",))],
    )

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    parser.set_default_command(func)
    assert parser.add_argument.mock_calls == [call("-x", help="%(default)s")]
    assert parser.set_defaults.mock_calls == [call(function=func)]


def test_set_default_command__declared_vs_signature__names_mismatch():
    def func(bar):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        (
            ParserAddArgumentSpec(
                func_arg_name="x",
                cli_arg_names=("foo",),
                nargs=argparse.ONE_OR_MORE,
                other_add_parser_kwargs={"choices": [1, 2], "help": "me"},
            ),
        ),
    )

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    with pytest.raises(
        AssemblingError, match="func: argument foo does not fit function signature: bar"
    ):
        argh.set_default_command(parser, func)


def test_set_default_command__declared_vs_signature__same_name_pos_vs_opt():
    def func(foo):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        (ParserAddArgumentSpec(func_arg_name="foo", cli_arg_names=("--foo",)),),
    )

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    import re

    with pytest.raises(
        AssemblingError,
        match=re.escape(
            'func: argument "foo" declared as positional (in function signature) and optional (via decorator)'
        ),
    ):
        argh.set_default_command(parser, func)


@pytest.fixture()
def big_command_with_everything():
    # TODO: split into small tests where we'd check each combo and make sure
    # they interact as expected (e.g. pos opt arg gets the short form even if
    # there's a pos req arg, etc.)
    #
    # an arg with a unique first letter per arg type + every combination
    # of conflicting first letters per every two arg types:
    # - positional required (i.e. without a default value)
    # - positional optional (i.e. with a default value)
    # - named-only required (i.e. kwonly without a default value)
    # - named-only optional (i.e. kwonly with a default value)
    def func(
        alpha_pos_req,
        beta_pos_req,
        alpha_pos_opt="alpha",
        beta_pos_opt_one="beta one",
        beta_pos_opt_two="beta two",
        gamma_pos_opt="gamma named",
        delta_pos_opt="delta named",
        theta_pos_opt="theta named",
        *args,
        gamma_kwonly_opt="gamma kwonly",
        delta_kwonly_req,
        epsilon_kwonly_req_one,
        epsilon_kwonly_req_two,
        zeta_kwonly_opt="zeta kwonly",
        **kwargs,
    ):
        return (
            alpha_pos_req,
            beta_pos_req,
            alpha_pos_opt,
            beta_pos_opt_one,
            beta_pos_opt_two,
            gamma_pos_opt,
            delta_pos_opt,
            theta_pos_opt,
            gamma_kwonly_opt,
            delta_kwonly_req,
            epsilon_kwonly_req_one,
            epsilon_kwonly_req_two,
            zeta_kwonly_opt,
            args,
            kwargs,
        )

    yield func


def test_set_default_command_infer_cli_arg_names_from_func_signature__policy_legacy(
    big_command_with_everything,
):
    name_mapping_policy = NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    argh.set_default_command(
        parser, big_command_with_everything, name_mapping_policy=name_mapping_policy
    )

    help_tmpl = argh.constants.DEFAULT_ARGUMENT_TEMPLATE
    assert parser.add_argument.mock_calls == [
        call("alpha-pos-req", help="%(default)s"),
        call("beta-pos-req", help="%(default)s"),
        call("-a", "--alpha-pos-opt", default="alpha", type=str, help=help_tmpl),
        call("--beta-pos-opt-one", default="beta one", type=str, help=help_tmpl),
        call("--beta-pos-opt-two", default="beta two", type=str, help=help_tmpl),
        call("--gamma-pos-opt", default="gamma named", type=str, help=help_tmpl),
        call("--delta-pos-opt", default="delta named", type=str, help=help_tmpl),
        call("-t", "--theta-pos-opt", default="theta named", type=str, help=help_tmpl),
        call("args", nargs=argparse.ZERO_OR_MORE, help=help_tmpl),
        call("--gamma-kwonly-opt", default="gamma kwonly", type=str, help=help_tmpl),
        call("delta-kwonly-req", help=help_tmpl),
        call("epsilon-kwonly-req-one", help=help_tmpl),
        call("epsilon-kwonly-req-two", help=help_tmpl),
        call(
            "-z", "--zeta-kwonly-opt", default="zeta kwonly", type=str, help=help_tmpl
        ),
    ]
    assert parser.set_defaults.mock_calls == [
        call(function=big_command_with_everything)
    ]


def test_set_default_command_infer_cli_arg_names_from_func_signature__policy_modern(
    big_command_with_everything,
):
    name_mapping_policy = NameMappingPolicy.BY_NAME_IF_KWONLY

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    argh.set_default_command(
        parser, big_command_with_everything, name_mapping_policy=name_mapping_policy
    )

    help_tmpl = argh.constants.DEFAULT_ARGUMENT_TEMPLATE
    assert parser.add_argument.mock_calls == [
        call("alpha-pos-req", help="%(default)s"),
        call("beta-pos-req", help="%(default)s"),
        call(
            "alpha-pos-opt",
            default="alpha",
            nargs=argparse.OPTIONAL,
            type=str,
            help=help_tmpl,
        ),
        call(
            "beta-pos-opt-one",
            default="beta one",
            nargs=argparse.OPTIONAL,
            type=str,
            help=help_tmpl,
        ),
        call(
            "beta-pos-opt-two",
            default="beta two",
            nargs=argparse.OPTIONAL,
            type=str,
            help=help_tmpl,
        ),
        call(
            "gamma-pos-opt",
            default="gamma named",
            nargs=argparse.OPTIONAL,
            type=str,
            help=help_tmpl,
        ),
        call(
            "delta-pos-opt",
            default="delta named",
            nargs=argparse.OPTIONAL,
            type=str,
            help=help_tmpl,
        ),
        call(
            "theta-pos-opt",
            default="theta named",
            nargs=argparse.OPTIONAL,
            type=str,
            help=help_tmpl,
        ),
        call("args", nargs=argparse.ZERO_OR_MORE, help=help_tmpl),
        call("--gamma-kwonly-opt", default="gamma kwonly", type=str, help=help_tmpl),
        call("--delta-kwonly-req", required=True, help=help_tmpl),
        call("--epsilon-kwonly-req-one", required=True, help=help_tmpl),
        call("--epsilon-kwonly-req-two", required=True, help=help_tmpl),
        call(
            "-z", "--zeta-kwonly-opt", default="zeta kwonly", type=str, help=help_tmpl
        ),
    ]
    assert parser.set_defaults.mock_calls == [
        call(function=big_command_with_everything)
    ]


def test_set_default_command_docstring():
    def func():
        "docstring"
        pass

    parser = argh.ArghParser()

    argh.set_default_command(parser, func)

    assert parser.description == "docstring"


def test_set_default_command__varkwargs_sharing_prefix():
    def func(*, alpha: str = "Alpha", aleph: str = "Aleph"): ...

    parser = argh.ArghParser()
    parser.add_argument = MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        call("--alpha", default="Alpha", type=str, help="%(default)s"),
        call("--aleph", default="Aleph", type=str, help="%(default)s"),
    ]


def test_add_subparsers_when_default_command_exists():
    def one():
        return 1

    def two():
        return 2

    def three():
        return 3

    p = argh.ArghParser()
    p.set_default_command(one)
    p.add_commands([two, three])

    ns_default = p.parse_args([])

    ns_explicit_two = p.parse_args(["two"])
    ns_explicit_three = p.parse_args(["three"])

    assert ns_default.get_function() == one
    assert ns_explicit_two.get_function() == two
    assert ns_explicit_three.get_function() == three


def test_set_default_command_when_subparsers_exist():
    def one():
        return 1

    def two():
        return 2

    def three():
        return 3

    p = argh.ArghParser()
    p.add_commands([one, two])
    p.set_default_command(three)

    ns_default = p.parse_args([])
    ns_explicit_one = p.parse_args(["one"])
    ns_explicit_two = p.parse_args(["two"])

    assert ns_explicit_one.get_function() == one
    assert ns_explicit_two.get_function() == two
    assert ns_default.get_function() == three


def test_set_add_commands_twice():
    def one():
        return 1

    def two():
        return 2

    p = argh.ArghParser()
    p.add_commands([one])
    p.add_commands([two])

    ns_explicit_one = p.parse_args(["one"])
    ns_explicit_two = p.parse_args(["two"])

    assert ns_explicit_one.get_function() == one
    assert ns_explicit_two.get_function() == two


def test_add_command_with_group_kwargs_but_no_group_name():
    def one():
        return 1

    p = argh.ArghParser()
    err_msg = "`group_kwargs` only makes sense with `group_name`"
    with pytest.raises(ValueError, match=err_msg):
        p.add_commands([one], group_kwargs={"help": "foo"})


def test_set_default_command_varargs():
    def func(*file_paths):
        yield ", ".join(file_paths)

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        call(
            "file-paths",
            nargs=argparse.ZERO_OR_MORE,
            help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE,
        ),
    ]


def test_set_default_command_kwargs():
    @argh.arg("foo")
    @argh.arg("--bar")
    def func(x, **kwargs):
        pass

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        call("x", help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
        call("foo", help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
        call("--bar", help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
    ]


def test_kwonlyargs__policy_legacy():
    "Correctly processing required and optional keyword-only arguments"

    def cmd(foo_pos, bar_pos, *args, foo_kwonly="foo_kwonly", bar_kwonly):
        return (foo_pos, bar_pos, args, foo_kwonly, bar_kwonly)

    parser = argh.ArghParser()
    parser.add_argument = MagicMock()
    parser.set_default_command(
        cmd, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT
    )
    help_tmpl = argh.constants.DEFAULT_ARGUMENT_TEMPLATE
    assert parser.add_argument.mock_calls == [
        call("foo-pos", help=help_tmpl),
        call("bar-pos", help=help_tmpl),
        call("args", nargs=argparse.ZERO_OR_MORE, help=help_tmpl),
        call("-f", "--foo-kwonly", default="foo_kwonly", type=str, help=help_tmpl),
        call("bar-kwonly", help=help_tmpl),
    ]


def test_kwonlyargs__policy_modern():
    "Correctly processing required and optional keyword-only arguments"

    def cmd(foo_pos, bar_pos, *args, foo_kwonly="foo_kwonly", bar_kwonly):
        return (foo_pos, bar_pos, args, foo_kwonly, bar_kwonly)

    parser = argh.ArghParser()
    parser.add_argument = MagicMock()
    parser.set_default_command(
        cmd, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_KWONLY
    )
    help_tmpl = argh.constants.DEFAULT_ARGUMENT_TEMPLATE
    assert parser.add_argument.mock_calls == [
        call("foo-pos", help=help_tmpl),
        call("bar-pos", help=help_tmpl),
        call("args", nargs=argparse.ZERO_OR_MORE, help=help_tmpl),
        call("-f", "--foo-kwonly", default="foo_kwonly", type=str, help=help_tmpl),
        call("-b", "--bar-kwonly", required=True, help=help_tmpl),
    ]


@patch("argh.assembling.COMPLETION_ENABLED", True)
def test_custom_argument_completer():
    "Issue #33: Enable custom per-argument shell completion"

    def func(foo):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        [
            ParserAddArgumentSpec(
                func_arg_name="foo", cli_arg_names=("foo",), completer="STUB"
            )
        ],
    )

    p = argh.ArghParser()
    p.set_default_command(func)

    assert p._actions[-1].completer == "STUB"


@patch("argh.assembling.COMPLETION_ENABLED", False)
def test_custom_argument_completer_no_backend():
    "If completion backend is not available, nothing breaks"

    def func(foo):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        [
            ParserAddArgumentSpec(
                func_arg_name="foo", cli_arg_names=("foo",), completer="STUB"
            )
        ],
    )

    p = argh.ArghParser()
    p.set_default_command(func)

    assert not hasattr(p._actions[-1], "completer")


@patch("argh.assembling.add_commands")
def test_add_subcommands(mock_add_commands):
    mock_parser = MagicMock()

    def get_items():
        pass

    argh.add_subcommands(
        mock_parser,
        "db",
        [get_items],
        title="database commands",
        help="CRUD for our silly database",
    )

    mock_add_commands.assert_called_with(
        mock_parser,
        [get_items],
        group_name="db",
        group_kwargs={
            "title": "database commands",
            "help": "CRUD for our silly database",
        },
    )


@patch("argh.helpers.autocomplete")
def test_arghparser_autocomplete_method(mock_autocomplete):
    p = argh.ArghParser()
    p.autocomplete()

    mock_autocomplete.assert_called()


def test_is_positional():
    with pytest.raises(ValueError, match="Expected at least one"):
        argh.assembling._is_positional([])
    with pytest.raises(ValueError, match="Expected at least one"):
        argh.assembling._is_positional([""])
    assert argh.assembling._is_positional(["f"]) is True
    assert argh.assembling._is_positional(["foo"]) is True
    assert argh.assembling._is_positional(["--foo"]) is False
    assert argh.assembling._is_positional(["-f"]) is False
    assert argh.assembling._is_positional(["-f", "--foo"]) is False

    # this spec is invalid but validation is out of scope of the function
    # as it only checks if the first argument has the leading dash
    assert argh.assembling._is_positional(["-f", "foo"]) is False


def test_typing_hints_only_used_when_arg_deco_not_used():
    @argh.arg("foo", type=int)
    def func_decorated(foo: Optional[float]): ...

    def func_undecorated(bar: Optional[float]): ...

    parser = argparse.ArgumentParser()
    parser.add_argument = MagicMock()
    argh.set_default_command(parser, func_decorated)
    assert parser.add_argument.mock_calls == [
        call("foo", type=int, help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument = MagicMock()
    argh.set_default_command(parser, func_undecorated)
    assert parser.add_argument.mock_calls == [
        call(
            "bar",
            nargs="?",
            type=float,
            help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE,
        ),
    ]


def test_typing_hints_overview():
    def func(
        alpha,
        beta: str,
        gamma: Optional[int] = None,
        *,
        delta: float = 1.5,
        epsilon: Optional[int] = 42,
        zeta: bool = False,
    ) -> str:
        return f"alpha={alpha}, beta={beta}, gamma={gamma}, delta={delta}, epsilon={epsilon}, zeta={zeta}"

    parser = argparse.ArgumentParser()
    parser.add_argument = MagicMock()
    argh.set_default_command(
        parser, func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_KWONLY
    )
    _extra_kw = {"help": argh.constants.DEFAULT_ARGUMENT_TEMPLATE}
    assert parser.add_argument.mock_calls == [
        call("alpha", **_extra_kw),
        call("beta", type=str, **_extra_kw),
        call("gamma", default=None, nargs="?", type=int, **_extra_kw),
        call("-d", "--delta", type=float, default=1.5, **_extra_kw),
        call("-e", "--epsilon", type=int, default=42, required=False, **_extra_kw),
        call("-z", "--zeta", default=False, action="store_true", **_extra_kw),
    ]


def test_typing_hints_str__policy_by_name_if_has_default():
    def func(alpha: str, beta: str = "N/A", *, gamma: str, delta: str = "N/A") -> str:
        return f"alpha={alpha}, beta={beta}, gamma={gamma}, delta={delta}"

    parser = argparse.ArgumentParser()
    parser.add_argument = MagicMock()
    argh.set_default_command(
        parser, func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT
    )
    _extra_kw = {"help": argh.constants.DEFAULT_ARGUMENT_TEMPLATE}
    assert parser.add_argument.mock_calls == [
        call("alpha", type=str, **_extra_kw),
        call("-b", "--beta", default="N/A", type=str, **_extra_kw),
        call("gamma", type=str, **_extra_kw),
        call("-d", "--delta", default="N/A", type=str, **_extra_kw),
    ]


def test_typing_hints_str__policy_by_name_if_kwonly():
    def func(alpha: str, beta: str = "N/A", *, gamma: str, delta: str = "N/A") -> str:
        return f"alpha={alpha}, beta={beta}, gamma={gamma}, delta={delta}"

    parser = argparse.ArgumentParser()
    parser.add_argument = MagicMock()
    argh.set_default_command(
        parser, func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_KWONLY
    )
    _extra_kw = {"help": argh.constants.DEFAULT_ARGUMENT_TEMPLATE}
    assert parser.add_argument.mock_calls == [
        call("alpha", type=str, help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
        call("beta", type=str, default="N/A", nargs="?", **_extra_kw),
        call("-g", "--gamma", required=True, type=str, **_extra_kw),
        call("-d", "--delta", default="N/A", type=str, **_extra_kw),
    ]


def test_typing_hints_bool__policy_by_name_if_has_default():
    def func(
        alpha: bool, beta: bool = False, *, gamma: bool, delta: bool = False
    ) -> str:
        return f"alpha={alpha}, beta={beta}, gamma={gamma}, delta={delta}"

    parser = argparse.ArgumentParser()
    parser.add_argument = MagicMock()
    argh.set_default_command(
        parser, func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT
    )
    _extra_kw = {"help": argh.constants.DEFAULT_ARGUMENT_TEMPLATE}
    assert parser.add_argument.mock_calls == [
        call("alpha", type=bool, **_extra_kw),
        call("-b", "--beta", default=False, action="store_true", **_extra_kw),
        call("gamma", type=bool, **_extra_kw),
        call("-d", "--delta", default=False, action="store_true", **_extra_kw),
    ]


def test_typing_hints_bool__policy_by_name_if_kwonly():
    def func(
        alpha: bool, beta: bool = False, *, gamma: bool, delta: bool = False
    ) -> str:
        return f"alpha={alpha}, beta={beta}, gamma={gamma}, delta={delta}"

    parser = argparse.ArgumentParser()
    parser.add_argument = MagicMock()
    argh.set_default_command(
        parser, func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_KWONLY
    )
    _extra_kw = {"help": argh.constants.DEFAULT_ARGUMENT_TEMPLATE}
    assert parser.add_argument.mock_calls == [
        call("alpha", type=bool, **_extra_kw),
        call("beta", type=bool, default=False, nargs="?", **_extra_kw),
        call("-g", "--gamma", required=True, type=bool, **_extra_kw),
        call("-d", "--delta", default=False, action="store_true", **_extra_kw),
    ]


def test_typing_hints_literal():
    def func(
        name: Literal["Alice", "Bob"], *, greeting: Literal["Hello", "Hi"] = "Hello"
    ) -> str:
        return f"{greeting}, {name}!"

    parser = argparse.ArgumentParser()
    parser.add_argument = MagicMock()
    argh.set_default_command(
        parser, func, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_KWONLY
    )
    _extra_kw = {"help": argh.constants.DEFAULT_ARGUMENT_TEMPLATE}
    assert parser.add_argument.mock_calls == [
        call("name", choices=("Alice", "Bob"), type=str, **_extra_kw),
        call(
            "-g",
            "--greeting",
            choices=("Hello", "Hi"),
            type=str,
            default="Hello",
            **_extra_kw,
        ),
    ]
