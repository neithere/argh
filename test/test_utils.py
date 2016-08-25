# coding: utf-8
"""
Unit Tests For Utility Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import functools
import sys

import pytest


from argh.utils import get_arg_spec


def function(x, y=0):
    return

def decorated(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        print("Wrapping function call")
        return f(*args, **kwargs)
    return wrapped


def _assert_spec(f, **overrides):
    spec = get_arg_spec(f)

    defaults = {
        'args': ['x', 'y'],
        'varargs': None,
        'varkw': None,
        'defaults': (0,),
        'kwonlyargs': [],
        'annotations': {},
    }

    for k in defaults:
        actual = getattr(spec, k)
        expected = overrides[k] if k in overrides else defaults[k]
        assert actual == expected


@pytest.mark.skipif(sys.version_info < (3,5),
                    reason="requires python3.5")
def test_get_arg_spec__plain_func():
    _assert_spec(function)


@pytest.mark.skipif(sys.version_info < (3,5),
                    reason="requires python3.5")
def test_get_arg_spec__decorated_func():
    def d(_f):
        return _f
    decorated = d(function)

    _assert_spec(decorated)


@pytest.mark.skipif(sys.version_info < (3,5),
                    reason="requires python3.5")
def test_get_arg_spec__wrapped():
    wrapped = decorated(function)
    _assert_spec(wrapped)


@pytest.mark.skipif(sys.version_info < (3,5),
                    reason="requires python3.5")
def test_get_arg_spec__wrapped_nested():
    wrapped = decorated(decorated(function))
    _assert_spec(wrapped)


@pytest.mark.skipif(sys.version_info < (3,5),
                    reason="requires python3.5")
def test_get_arg_spec__wrapped_complex():
    def wrapper_deco(outer_arg):
        def _outer(f):
            @functools.wraps(f)
            def _inner(*args, **kwargs):
                return f(*args, **kwargs)
            return _inner
        return _outer

    wrapped = wrapper_deco(5)(function)

    _assert_spec(wrapped)


@pytest.mark.skipif(sys.version_info < (3,5),
                    reason="requires python3.5")
def test_get_arg_spec__static_method():
    class C:
        @staticmethod
        def f(x, y=0):
            return x

    _assert_spec(C.f)


@pytest.mark.skipif(sys.version_info < (3,5),
                    reason="requires python3.5")
def test_get_arg_spec__method():
    class C:
        def f(self, x, y=0):
            return x

    _assert_spec(C.f, args=['self', 'x', 'y'])
