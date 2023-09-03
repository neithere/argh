"""
Unit Tests For Assembling Phase
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from unittest.mock import MagicMock, call, patch

import pytest

import argh


def test_guess_type_from_choices():
    old = dict(option_strings=("foo",), choices=[1, 2])
    new = dict(option_strings=("foo",), choices=[1, 2], type=int)
    assert new == argh.assembling._guess(old)

    # ensure no overrides
    same = dict(option_strings=("foo",), choices=[1, 2], type="NO_MATTER_WHAT")
    assert same == argh.assembling._guess(same)


def test_guess_type_from_default():
    old = dict(option_strings=("foo",), default=1)
    new = dict(option_strings=("foo",), default=1, type=int)
    assert new == argh.assembling._guess(old)

    # ensure no overrides
    same = dict(option_strings=("foo",), default=1, type="NO_MATTER_WHAT")
    assert same == argh.assembling._guess(same)


def test_guess_action_from_default():
    # True → store_false
    old = dict(option_strings=("foo",), default=False)
    new = dict(option_strings=("foo",), default=False, action="store_true")
    assert new == argh.assembling._guess(old)

    # True → store_false
    old = dict(option_strings=("foo",), default=True)
    new = dict(option_strings=("foo",), default=True, action="store_false")
    assert new == argh.assembling._guess(old)

    # ensure no overrides
    same = dict(option_strings=("foo",), default=False, action="NO_MATTER_WHAT")
    assert same == argh.assembling._guess(same)


def test_set_default_command():
    def func():
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        (
            dict(option_strings=("foo",), nargs="+", choices=[1, 2], help="me"),
            dict(
                option_strings=(
                    "-b",
                    "--bar",
                ),
                default=False,
            ),
        ),
    )

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        call("foo", nargs="+", choices=[1, 2], help="me", type=int),
        call(
            "-b",
            "--bar",
            default=False,
            action="store_true",
            help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE,
        ),
    ]
    assert parser.set_defaults.mock_calls == [call(function=func)]


def test_set_default_command_infer_cli_arg_names_from_func_signature():
    # TODO: split into small tests where we'd check each combo and make sure
    # they interact as expected (e.g. pos opt arg gets the short form even if
    # there's a pos req arg, etc.)
    #
    # an arg with a unique first letter per arg type + every combination
    # of conflicting first letters per every two arg types:
    # - positional required (i.e. without a default value)
    # - positional optional (i.e. with a default value)
    # - named-only required (i.e. kwonly without a default value)
    # - named-only optional (i.e. kwonly with a default valu)
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
            gamma_kwonly_opt,
            delta_kwonly_req,
            epsilon_kwonly_req_one,
            epsilon_kwonly_req_two,
            zeta_kwonly_opt,
            args,
            kwargs,
        )

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()
    parser.set_defaults = MagicMock()

    argh.set_default_command(parser, func)

    help_tmpl = argh.constants.DEFAULT_ARGUMENT_TEMPLATE
    assert parser.add_argument.mock_calls == [
        call("alpha_pos_req", help="%(default)s"),
        call("beta_pos_req", help="%(default)s"),
        call("-a", "--alpha-pos-opt", default="alpha", type=str, help=help_tmpl),
        call("--beta-pos-opt-one", default="beta one", type=str, help=help_tmpl),
        call("--beta-pos-opt-two", default="beta two", type=str, help=help_tmpl),
        call("--gamma-pos-opt", default="gamma named", type=str, help=help_tmpl),
        call("--delta-pos-opt", default="delta named", type=str, help=help_tmpl),
        call("-t", "--theta-pos-opt", default="theta named", type=str, help=help_tmpl),
        call("--gamma-kwonly-opt", default="gamma kwonly", type=str, help=help_tmpl),
        call("--delta-kwonly-req", required=True, help=help_tmpl),
        call("--epsilon-kwonly-req-one", required=True, help=help_tmpl),
        call("--epsilon-kwonly-req-two", required=True, help=help_tmpl),
        call(
            "-z", "--zeta-kwonly-opt", default="zeta kwonly", type=str, help=help_tmpl
        ),
        call("args", nargs="*", help=help_tmpl),
    ]
    assert parser.set_defaults.mock_calls == [call(function=func)]


def test_set_default_command_docstring():
    def func():
        "docstring"
        pass

    parser = argh.ArghParser()

    argh.set_default_command(parser, func)

    assert parser.description == "docstring"


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


def test_add_command_with_group_kwargs_but_no_group_name():
    def one():
        return 1

    p = argh.ArghParser()
    err_msg = "`group_kwargs` only makes sense with `group_name`"
    with pytest.raises(ValueError, match=err_msg):
        p.add_commands([one], group_kwargs={"help": "foo"})


def test_set_default_command_mixed_arg_types():
    def func():
        pass

    setattr(func, argh.constants.ATTR_ARGS, [dict(option_strings=("x", "--y"))])

    p = argh.ArghParser()

    with pytest.raises(argh.AssemblingError) as excinfo:
        p.set_default_command(func)
    msg = "func: cannot add x/--y: invalid option string"
    assert msg in str(excinfo.value)


def test_set_default_command_varargs():
    def func(*file_paths):
        yield ", ".join(file_paths)

    parser = argh.ArghParser()

    parser.add_argument = MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        call("file_paths", nargs="*", help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
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


# TODO: remove in v.0.30
def test_annotation():
    "Extracting argument help from function annotations."

    def cmd(foo: "quux" = 123):  # noqa: F821
        pass

    parser = argh.ArghParser()

    with pytest.warns(DeprecationWarning, match="will be removed in Argh 0.30"):
        parser.set_default_command(cmd)

    prog_help = parser.format_help()

    assert "quux" in prog_help


def test_kwonlyargs():
    "Correctly processing required and optional keyword-only arguments"

    def cmd(foo_pos, bar_pos, *args, foo_kwonly="foo_kwonly", bar_kwonly):
        return (foo_pos, bar_pos, args, foo_kwonly, bar_kwonly)

    p = argh.ArghParser()
    p.add_argument = MagicMock()
    p.set_default_command(cmd)
    help_tmpl = argh.constants.DEFAULT_ARGUMENT_TEMPLATE
    assert p.add_argument.mock_calls == [
        call("foo_pos", help=help_tmpl),
        call("bar_pos", help=help_tmpl),
        call("-f", "--foo-kwonly", default="foo_kwonly", type=str, help=help_tmpl),
        call("-b", "--bar-kwonly", required=True, help=help_tmpl),
        call("args", nargs="*", help=help_tmpl),
    ]


@patch("argh.assembling.COMPLETION_ENABLED", True)
def test_custom_argument_completer():
    "Issue #33: Enable custom per-argument shell completion"

    def func(foo):
        pass

    setattr(
        func,
        argh.constants.ATTR_ARGS,
        [dict(option_strings=("foo",), completer="STUB")],
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
        [dict(option_strings=("foo",), completer="STUB")],
    )

    p = argh.ArghParser()
    p.set_default_command(func)

    assert not hasattr(p._actions[-1], "completer")


# TODO: remove in v.0.30
def test_set_default_command_deprecation_warnings():
    parser = argh.ArghParser()

    with pytest.warns(
        DeprecationWarning, match="Argument `title` is deprecated in add_commands()"
    ):
        argh.add_commands(parser, [], group_name="a", title="bar")

    with pytest.warns(
        DeprecationWarning,
        match="Argument `description` is deprecated in add_commands()",
    ):
        argh.add_commands(parser, [], group_name="b", description="bar")

    with pytest.warns(
        DeprecationWarning, match="Argument `help` is deprecated in add_commands()"
    ):
        argh.add_commands(parser, [], group_name="c", help="bar")


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
