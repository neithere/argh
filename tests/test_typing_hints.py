from typing import List, Optional, Union

import pytest

from argh.assembling import TypingHintArgSpecGuesser


@pytest.mark.parametrize("arg_type", TypingHintArgSpecGuesser.BASIC_TYPES)
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
    assert guess(Optional[list]) == {"nargs": "*", "required": False}

    assert guess(List[str]) == {"nargs": "*", "type": str}
    assert guess(List[int]) == {"nargs": "*", "type": int}
    assert guess(Optional[List[str]]) == {"nargs": "*", "type": str, "required": False}
    assert guess(Optional[List[tuple]]) == {"nargs": "*", "required": False}

    assert guess(List[list]) == {"nargs": "*"}
    assert guess(List[tuple]) == {"nargs": "*"}


@pytest.mark.parametrize("arg_type", (dict, tuple))
def test_unusable_types(arg_type):
    guess = TypingHintArgSpecGuesser.typing_hint_to_arg_spec_params

    assert guess(arg_type) == {}
