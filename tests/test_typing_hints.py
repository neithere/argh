from types import UnionType
from typing import Any, get_args, get_origin, Union

import pytest


BASIC_TYPES = (str, int, float, bool)


@pytest.mark.parametrize("arg_type", BASIC_TYPES)
def test_simple_types(arg_type):
    # just the basic type
    assert typing_hint_to_arg_spec_params(arg_type) == {
        "type": arg_type
    }

    # basic type or None
    assert typing_hint_to_arg_spec_params(arg_type | None) == {
        "type": arg_type,
        "required": False
    }
    assert typing_hint_to_arg_spec_params(None | arg_type) == {
#       "type": arg_type,
        "required": False
    }

    # multiple basic types: the first one is used and None is looked up
    assert typing_hint_to_arg_spec_params(arg_type | str | None) == {
        "type": arg_type,
        "required": False
    }
    assert typing_hint_to_arg_spec_params(str | arg_type | None) == {
        "type": str,
        "required": False
    }


def test_list():
    assert typing_hint_to_arg_spec_params(list) == {"nargs": "*"}
    assert typing_hint_to_arg_spec_params(list | None) == {"nargs": "*", "required": False}

    assert typing_hint_to_arg_spec_params(list[str]) == {"nargs": "*", "type": str}
    assert typing_hint_to_arg_spec_params(list[str] | None) == {"nargs": "*", "type": str, "required": False}

    assert typing_hint_to_arg_spec_params(list[str, int]) == {"nargs": "*", "type": str}
    assert typing_hint_to_arg_spec_params(list[str, int] | None) == {
        "nargs": "*",
        "type": str,
        "required": False
    }
#   assert typing_hint_to_arg_spec_params(list[str | None]) == {
#       "type": str,
#       "nargs": "*",
#   }
#   assert typing_hint_to_arg_spec_params(list[str | None] | None) == {
#       "type": str,
#       "nargs": "+",
#       "required": False
#   }

    assert typing_hint_to_arg_spec_params(list[list]) == {
        "nargs": "*",
    }
    assert typing_hint_to_arg_spec_params(list[list, str]) == {
        "nargs": "*",
    }
    assert typing_hint_to_arg_spec_params(list[tuple]) == {
        "nargs": "*",
    }


@pytest.mark.parametrize("arg_type", (dict, tuple))
def test_unusable_types(arg_type):
    assert typing_hint_to_arg_spec_params(arg_type) == {}


def typing_hint_to_arg_spec_params(type_def: type) -> dict[str, Any]:
    origin = get_origin(type_def)
    args = get_args(type_def)

    print("--------------------------------")
    print(f"PARSE type_def: {type_def}, origin: {origin}, args: {args}")

    #if not origin and not args and type_def in BASIC_TYPES:
    if type_def in BASIC_TYPES:
        print("* basic type")
        return {
            "type": type_def
            #"type": _parse_basic_type(type_def)
        }

    if type_def == list:
        print("* list (no nested types)")
        return {"nargs": "*"}

    if origin == UnionType:
        print("* union")
        #return _parse_union_type(args)
        retval = {}
        #first_subtype = [t for t in args if not isinstance(None, t)][0]
        first_subtype = args[0]
        print("first_subtype", first_subtype)
        if first_subtype in BASIC_TYPES:
            retval["type"] = first_subtype

        if first_subtype == list:
            retval["nargs"] = "*"

        if get_origin(first_subtype) == list:
            retval["nargs"] = "*"
            item_type = _extract_item_type_from_list_type(first_subtype)
            print(f"item type {item_type}")
            if item_type:
                retval["type"] = item_type

        if type(None) in args:
            retval["required"] = False
        return retval

    if origin == list:
        print("* list (with nested types)")
        retval = {}
        retval["nargs"] = "*"
        print(f"item type {args[0]}")
        if args[0] in BASIC_TYPES:
            retval["type"] = args[0]
        return retval

    print("huh??")
    return {}


def _extract_item_type_from_list_type(type_def) -> type | None:
    print("_extract_item_type_from_list_type", type_def)
    args = get_args(type_def)
    if not args:
        return
    if args[0] in BASIC_TYPES:
        return args[0]
    return None


#   if origin == Union:
#       return _parse_union_type(get_args(type_def))

#   if origin == list:
#       return _parse_list_type(get_args(type_def))

#   parsed_single = _parse_concrete_typ

#   if origin in (str, int, float, bool):
#       return origin
#   if origin == list:


#def _parse_basic_type(type_def: type) -> dict[str, Any]:
#    print("parse basic type", type_def)
#    return type_def


def _parse_union_type(types: list[type]) -> dict[str, Any]:
    print("parse union type", types)
    return {
        "type": [t for t in types if not isinstance(None, t)][0],
        "required": type(None) not in types,
    }


def _parse_list_type(types: list[type]) -> dict[str, Any]:
    print("parse list type", types)
    if types:
        # just take the first item
        return {
            "type": types[0]
        }
    return {}
