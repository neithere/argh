"""
Unit Tests For Utility Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import functools

from argh.utils import get_arg_spec, unindent


def function(x, y=0):
    return


def decorated(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        print("Wrapping function call")
        return func(*args, **kwargs)

    return wrapped


def _assert_spec(func, **overrides):
    spec = get_arg_spec(func)

    defaults = {
        "args": ["x", "y"],
        "varargs": None,
        "varkw": None,
        "defaults": (0,),
        "kwonlyargs": [],
        "annotations": {},
    }

    for k in defaults:
        actual = getattr(spec, k)
        expected = overrides[k] if k in overrides else defaults[k]
        assert actual == expected


def test_get_arg_spec__plain_func():
    _assert_spec(function)


def test_get_arg_spec__decorated_func():
    def d(_f):
        return _f

    decorated = d(function)

    _assert_spec(decorated)


def test_get_arg_spec__wrapped():
    wrapped = decorated(function)
    _assert_spec(wrapped)


def test_get_arg_spec__wrapped_nested():
    wrapped = decorated(decorated(function))
    _assert_spec(wrapped)


def test_get_arg_spec__wrapped_complex():
    def wrapper_deco(outer_arg):
        def _outer(func):
            @functools.wraps(func)
            def _inner(*args, **kwargs):
                return func(*args, **kwargs)

            return _inner

        return _outer

    wrapped = wrapper_deco(5)(function)

    _assert_spec(wrapped)


def test_get_arg_spec__static_method():
    class C:
        @staticmethod
        def func(x, y=0):
            return x

    _assert_spec(C.func)


def test_get_arg_spec__method():
    class C:
        def func(self, x, y=0):
            return x

    _assert_spec(C.func, args=["self", "x", "y"])


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
