"""
Unit Tests For the Argument DTO
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from argh.dto import ParserAddArgumentSpec


def test_update_empty_dto() -> None:
    def stub_completer(): ...

    dto = ParserAddArgumentSpec(
        func_arg_name="foo",
        cli_arg_names=["-f"],
    )
    other_dto = ParserAddArgumentSpec(
        func_arg_name="bar",
        cli_arg_names=["-f", "--foo"],
        is_required=True,
        default_value=123,
        nargs="+",
        other_add_parser_kwargs={"knights": "Ni!"},
        completer=stub_completer,
    )

    dto.update(other_dto)

    assert dto == ParserAddArgumentSpec(
        func_arg_name="foo",
        cli_arg_names=["-f", "--foo"],
        is_required=True,
        default_value=123,
        nargs="+",
        other_add_parser_kwargs={"knights": "Ni!"},
        completer=stub_completer,
    )


def test_update_full_dto() -> None:
    def stub_completer_one(): ...

    def stub_completer_two(): ...

    dto = ParserAddArgumentSpec(
        func_arg_name="foo",
        cli_arg_names=["-f"],
        nargs="?",
        is_required=True,
        default_value=123,
        other_add_parser_kwargs={"'tis but a": "scratch"},
        completer=stub_completer_one,
    )
    other_dto = ParserAddArgumentSpec(
        func_arg_name="bar",
        cli_arg_names=["-f", "--foo"],
        nargs="+",
        is_required=False,
        default_value=None,
        other_add_parser_kwargs={"knights": "Ni!"},
        completer=stub_completer_two,
    )

    dto.update(other_dto)

    assert dto == ParserAddArgumentSpec(
        func_arg_name="foo",
        cli_arg_names=["-f", "--foo"],
        is_required=False,
        default_value=None,
        nargs="+",
        other_add_parser_kwargs={"knights": "Ni!", "'tis but a": "scratch"},
        completer=stub_completer_two,
    )


class TestGetAllKwargs: ...


def test_make_from_kwargs_minimal() -> None:
    dto = ParserAddArgumentSpec.make_from_kwargs("foo", ["-f", "--foo"], {})

    assert dto == ParserAddArgumentSpec(
        func_arg_name="foo", cli_arg_names=["-f", "--foo"]
    )


def test_make_from_kwargs_full() -> None:
    dto = ParserAddArgumentSpec.make_from_kwargs(
        "foo",
        ["-f", "--foo"],
        {
            "action": "some action",
            "nargs": "?",
            "default": None,
            "type": str,
            "choices": [1, 2, 3],
            "required": False,
            "help": "some help",
            "metavar": "FOOOOO",
            "dest": "foo_dest",
            "some arbitrary key": "and its value",
        },
    )

    assert dto == ParserAddArgumentSpec(
        func_arg_name="foo",
        cli_arg_names=["-f", "--foo"],
        is_required=False,
        default_value=None,
        nargs="?",
        other_add_parser_kwargs={
            "action": "some action",
            "type": str,
            "choices": [1, 2, 3],
            "help": "some help",
            "metavar": "FOOOOO",
            "dest": "foo_dest",
            "some arbitrary key": "and its value",
        },
    )
