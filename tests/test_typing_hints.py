from pathlib import Path
from typing import List, Literal, Optional, Union

import pytest

from argh.assembling import TypingHintArgSpecGuesser


class CustomSimpleType:
    def __init__(self, string: str) -> None: ...


@pytest.mark.parametrize("arg_type", (str, int, float, bool, Path, CustomSimpleType))
def test_simple_types(arg_type):
    guess = TypingHintArgSpecGuesser.typing_hint_to_arg_spec_params

    # just the basic type
    assert guess(arg_type) == {"type": arg_type}

    # basic type or None
    assert guess(Optional[arg_type]) == {
        "type": arg_type,
        "required": False,
    }
    assert guess(Union[None, arg_type]) == {"required": False}

    # multiple basic types: the first one is used and None is looked up
    assert guess(Union[arg_type, str, None]) == {
        "type": arg_type,
        "required": False,
    }
    assert guess(Union[str, arg_type, None]) == {
        "type": str,
        "required": False,
    }


def test_list():
    guess = TypingHintArgSpecGuesser.typing_hint_to_arg_spec_params

    assert guess(list) == {"nargs": "*"}
    assert guess(List) == {"nargs": "*"}
    assert guess(Optional[list]) == {"nargs": "*", "required": False}
    assert guess(Optional[List]) == {"nargs": "*", "required": False}

    assert guess(List[str]) == {"nargs": "*", "type": str}
    assert guess(List[int]) == {"nargs": "*", "type": int}
    assert guess(Optional[List[str]]) == {"nargs": "*", "type": str, "required": False}
    assert guess(Optional[List[tuple]]) == {"nargs": "*", "required": False}

    assert guess(List[list]) == {"nargs": "*"}
    assert guess(List[tuple]) == {"nargs": "*"}

    assert guess(List[Path]) == {"nargs": "*", "type": Path}
    assert guess(List[CustomSimpleType]) == {"nargs": "*", "type": CustomSimpleType}


def test_literal():
    guess = TypingHintArgSpecGuesser.typing_hint_to_arg_spec_params

    assert guess(Literal["a"]) == {"choices": ("a",), "type": str}
    assert guess(Literal["a", "b"]) == {"choices": ("a", "b"), "type": str}
    assert guess(Literal[1]) == {"choices": (1,), "type": int}


@pytest.mark.parametrize(
    "arg_type, expected",
    [
        (dict, {"type": dict}),
        (tuple, {"nargs": "*"}),
    ],
)
def test_unusable_types(arg_type, expected):
    guess = TypingHintArgSpecGuesser.typing_hint_to_arg_spec_params
    assert guess(arg_type) == expected
