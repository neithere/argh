from typing import List, Literal, Optional, Union

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
    assert guess(List) == {"nargs": "*"}
    assert guess(Optional[list]) == {"nargs": "*", "required": False}
    assert guess(Optional[List]) == {"nargs": "*", "required": False}

    assert guess(List[str]) == {"nargs": "*", "type": str}
    assert guess(List[int]) == {"nargs": "*", "type": int}
    assert guess(Optional[List[str]]) == {"nargs": "*", "type": str, "required": False}
    assert guess(Optional[List[tuple]]) == {"nargs": "*", "required": False}

    assert guess(List[list]) == {"nargs": "*"}
    assert guess(List[tuple]) == {"nargs": "*"}


def test_literal():
    guess = TypingHintArgSpecGuesser.typing_hint_to_arg_spec_params

    assert guess(Literal["a"]) == {"choices": ("a",), "type": str}
    assert guess(Literal["a", "b"]) == {"choices": ("a", "b"), "type": str}
    assert guess(Literal[1]) == {"choices": (1,), "type": int}


@pytest.mark.parametrize("arg_type", (dict, tuple))
def test_unusable_types(arg_type):
    guess = TypingHintArgSpecGuesser.typing_hint_to_arg_spec_params

    assert guess(arg_type) == {}


# ------------------------------------------------------------------------------
# Test type hints on combinations of generics

from typing import (
    Dict, Tuple, Mapping, MutableMapping, DefaultDict, ChainMap, OrderedDict,
    Callable, Optional, List
)

DFLT_MULTI_PARAM_TYPES = (
    Dict, Tuple, Mapping, MutableMapping, DefaultDict, ChainMap, OrderedDict
)

def type_combos(
        generic_types, 
        type_variables=None,
        *,
        multi_param_types=DFLT_MULTI_PARAM_TYPES
    ):
    """
    Generate "generic" using combinations of types such as 
        `Optional[List], Dict[Tuple, List], Callable[[List], Dict]`
    from a list of generic types such as `Optional`, `List`, `Dict`, `Callable`
    and a list of type variables that are used to parametrize these generic types.
    
    :param generic_types: A list of generic types
    :param type_variables: A list of type variables
    :return: A generator that yields generic types

    >>> from typing import Optional, Dict, Tuple, List, Callable
    >>> list(type_combos([Optional, Tuple], [list, dict]))  # doctest: +NORMALIZE_WHITESPACE
    [typing.Optional[list], typing.Optional[dict], 
    typing.Tuple[list, dict], typing.Tuple[dict, list]]

    More significant example:

    >>> generic_types = [Optional, Callable, Dict, Tuple]
    >>> type_variables = [tuple, dict, List]
    >>>
    >>> for combo in type_combos(generic_types, type_variables):
    ...     print(combo)
    typing.Optional[tuple]
    typing.Optional[dict]
    typing.Optional[typing.List]
    typing.Callable[[typing.Tuple[dict, ...]], tuple]
    typing.Callable[[typing.Tuple[typing.List, ...]], tuple]
    typing.Callable[[typing.Tuple[dict, typing.List]], tuple]
    typing.Callable[[typing.Tuple[typing.List, dict]], tuple]
    typing.Callable[[typing.Tuple[tuple, ...]], dict]
    typing.Callable[[typing.Tuple[typing.List, ...]], dict]
    typing.Callable[[typing.Tuple[tuple, typing.List]], dict]
    typing.Callable[[typing.Tuple[typing.List, tuple]], dict]
    typing.Callable[[typing.Tuple[tuple, ...]], typing.List]
    typing.Callable[[typing.Tuple[dict, ...]], typing.List]
    typing.Callable[[typing.Tuple[tuple, dict]], typing.List]
    typing.Callable[[typing.Tuple[dict, tuple]], typing.List]
    typing.Dict[tuple, dict]
    typing.Dict[tuple, typing.List]
    typing.Dict[dict, tuple]
    typing.Dict[dict, typing.List]
    typing.Dict[typing.List, tuple]
    typing.Dict[typing.List, dict]
    typing.Tuple[tuple, dict]
    typing.Tuple[tuple, typing.List]
    typing.Tuple[dict, tuple]
    typing.Tuple[dict, typing.List]
    typing.Tuple[typing.List, tuple]
    typing.Tuple[typing.List, dict]
    """
    from itertools import permutations
    
    if type_variables is None:
        type_variables = list(generic_types)
        
    def generate_combos(generic_type, remaining_vars):
        if generic_type is Callable:
            # Separate one variable for the output type
            for output_type in remaining_vars:
                input_vars = [var for var in remaining_vars if var != output_type]
                # Generate combinations of input types
                for n in range(1, len(input_vars) + 1):
                    for input_combo in permutations(input_vars, n):
                        # Format single-element tuples correctly
                        if len(input_combo) == 1:
                            input_type = Tuple[input_combo[0], ...]
                        else:
                            input_type = Tuple[input_combo]
                        yield Callable[[input_type], output_type]
        elif generic_type in multi_param_types:
            required_params = 2  # These types generally require two type parameters
            for combo in permutations(remaining_vars, required_params):
                yield generic_type[combo]
        else:
            for type_var in remaining_vars:
                yield generic_type[type_var]
    for generic_type in generic_types:
        yield from generate_combos(generic_type, type_variables)


def issue_216_happens_annotations(func, annotation):
    """
    Util to test what annotations make the 
        https://github.com/neithere/argh/issues/216 
    issue happen
    """
    import argh
    func.__annotations__['x'] = annotation
    try:
        argh.dispatch_command(func)
    except IndexError as e:
        if e.args[0] == 'tuple index out of range':
             return True
    except BaseException:
         pass
    return False


# TODO: Use pytest.mark.parametrize?
def test_that_issue_216_does_not_happen(
        generic_types=(Dict, Tuple, OrderedDict, Callable, Optional, List),
        type_variables=None
    ):
    """
    Test that the issue 216 happens with the annotations
    that we expect it to happen.

    NOTE: This takes ~18s to run on my side. 
        Could reduce the number of generic_types and type_variables to accelerate.
        (The current settings lead to 109_776 combinations being tested.
    """
    from functools import partial

    if type_variables is None:
        type_variables = list(set(generic_types) - {Optional}) + [int, str, float]

    combos = list(type_combos(generic_types, type_variables))

    def func(x = None):
            return None

    there_is_an_issue = partial(issue_216_happens_annotations, func)

    failed = list(map(there_is_an_issue, combos))

    failed_combos = [typ for typ, failed_ in zip(combos, failed) if failed_]
    assert not failed_combos, f"There were some failed type combos: {failed_combos=}"