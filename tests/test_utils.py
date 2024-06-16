"""
Unit Tests For Utility Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from argparse import ArgumentParser, _SubParsersAction

import pytest

from argh.utils import SubparsersNotDefinedError, get_subparsers, unindent


def test_util_unindent():
    "Self-test the unindent() helper function"

    # target case
    one = """
    a
     b
      c
    """
    assert (
        unindent(one)
        == """
a
 b
  c
"""
    )

    # edge case: lack of indentation on first non-empty line
    two = """
a
  b
    c
"""

    assert unindent(two) == two

    # edge case: unexpectedly unindented in between
    three = """
    a
b
    c
    """

    assert (
        unindent(three)
        == """
a
b
c
"""
    )


def test_get_subparsers_existing() -> None:
    parser = ArgumentParser()
    parser.add_subparsers(help="hello")
    sub_parsers_action = get_subparsers(parser)
    assert isinstance(sub_parsers_action, _SubParsersAction)
    assert sub_parsers_action.help == "hello"


def test_get_subparsers_create() -> None:
    parser = ArgumentParser()
    sub_parsers_action = get_subparsers(parser, create=True)
    assert isinstance(sub_parsers_action, _SubParsersAction)


def test_get_subparsers_error() -> None:
    parser = ArgumentParser()
    with pytest.raises(SubparsersNotDefinedError):
        get_subparsers(parser)
