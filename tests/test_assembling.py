"""
Unit Tests For Assembling Phase
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from unittest import mock

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

    parser.add_argument = mock.MagicMock()
    parser.set_defaults = mock.MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        mock.call("foo", nargs="+", choices=[1, 2], help="me", type=int),
        mock.call(
            "-b",
            "--bar",
            default=False,
            action="store_true",
            help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE,
        ),
    ]
    assert parser.set_defaults.mock_calls == [mock.call(function=func)]


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


def test_add_command_with_namespace_kwargs_but_no_namespace_name():
    def one():
        return 1

    p = argh.ArghParser()
    err_msg = "`parser_kwargs` only makes sense with `namespace`"
    with pytest.raises(ValueError, match=err_msg):
        p.add_commands([one], namespace_kwargs={"help": "foo"})


def test_set_default_command_mixed_arg_types():
    def func():
        pass

    setattr(func, argh.constants.ATTR_ARGS, [dict(option_strings=("x", "--y"))])

    p = argh.ArghParser()

    with pytest.raises(ValueError) as excinfo:
        p.set_default_command(func)
    msg = "func: cannot add arg x/--y: invalid option string"
    assert msg in str(excinfo.value)


def test_set_default_command_varargs():
    def func(*file_paths):
        yield ", ".join(file_paths)

    parser = argh.ArghParser()

    parser.add_argument = mock.MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        mock.call(
            "file_paths", nargs="*", help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE
        ),
    ]


def test_set_default_command_kwargs():
    @argh.arg("foo")
    @argh.arg("--bar")
    def func(x, **kwargs):
        pass

    parser = argh.ArghParser()

    parser.add_argument = mock.MagicMock()

    argh.set_default_command(parser, func)

    assert parser.add_argument.mock_calls == [
        mock.call("x", help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
        mock.call("foo", help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
        mock.call("--bar", help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
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
    ns = {}
    exec("def cmd(*args, foo='abcd', bar):\n" "    return (args, foo, bar)", None, ns)
    cmd = ns["cmd"]
    p = argh.ArghParser()
    p.add_argument = mock.MagicMock()
    p.set_default_command(cmd)
    assert p.add_argument.mock_calls == [
        mock.call(
            "-f",
            "--foo",
            type=str,
            default="abcd",
            help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE,
        ),
        mock.call(
            "-b", "--bar", required=True, help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE
        ),
        mock.call("args", nargs="*", help=argh.constants.DEFAULT_ARGUMENT_TEMPLATE),
    ]


@mock.patch("argh.assembling.COMPLETION_ENABLED", True)
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


@mock.patch("argh.assembling.COMPLETION_ENABLED", False)
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


def test_set_default_command_deprecation_warnings():
    parser = argh.ArghParser()

    with pytest.warns(
        DeprecationWarning, match="Argument `title` is deprecated in add_commands()"
    ):
        argh.add_commands(parser, [], namespace="a", title="bar")

    with pytest.warns(
        DeprecationWarning,
        match="Argument `description` is deprecated in add_commands()",
    ):
        argh.add_commands(parser, [], namespace="b", description="bar")

    with pytest.warns(
        DeprecationWarning, match="Argument `help` is deprecated in add_commands()"
    ):
        argh.add_commands(parser, [], namespace="c", help="bar")


@mock.patch("argh.assembling.add_commands")
def test_add_subcommands(mock_add_commands):
    mock_parser = mock.MagicMock()

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
        namespace="db",
        namespace_kwargs={
            "title": "database commands",
            "help": "CRUD for our silly database",
        },
    )


@mock.patch("argh.helpers.autocomplete")
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
