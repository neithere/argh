# -*- coding: utf-8 -*-
"""
Unit Tests For Decorators
~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import argh


def test_aliases():
    @argh.aliases('one', 'two')
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_ALIASES)
    assert attr == ('one', 'two')


def test_arg():
    @argh.arg('foo', help='help', nargs='+')
    @argh.arg('--bar', default=1)
    def func():
        pass

    attrs = getattr(func, argh.constants.ATTR_ARGS)
    assert attrs == [
        dict(option_strings=('foo',), help='help', nargs='+'),
        dict(option_strings=('--bar',), default=1),
    ]


def test_named():
    @argh.named('new-name')
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_NAME)
    assert attr == 'new-name'


def test_named_proxy():
    @argh.named('new-name')
    def func(self):
        pass

    proxied_func = argh.named('another-name')(func)

    assert getattr(func, argh.constants.ATTR_NAME) == 'new-name'
    assert getattr(proxied_func, argh.constants.ATTR_NAME) == 'another-name'


def test_named_method():
    class A:
        @argh.named('new-name')
        def meth(self):
            pass

    assert getattr(A.meth, argh.constants.ATTR_NAME) == 'new-name'
    assert getattr(A().meth, argh.constants.ATTR_NAME) == 'new-name'


def test_named_method_proxy():
    class A:
        @argh.named('new-name')
        def meth(self):
            pass

    a = A()
    proxied_meth = argh.named('another-name')(a.meth)
    assert getattr(a.meth, argh.constants.ATTR_NAME) == 'new-name'
    assert getattr(proxied_meth, argh.constants.ATTR_NAME) == 'another-name'


def test_command():
    @argh.command
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_INFER_ARGS_FROM_SIGNATURE)
    assert attr == True


def test_wrap_errors():
    @argh.wrap_errors([KeyError, ValueError])
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_WRAPPED_EXCEPTIONS)
    assert attr == [KeyError, ValueError]


def test_wrap_errors_processor():
    @argh.wrap_errors(processor='STUB')
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_WRAPPED_EXCEPTIONS_PROCESSOR)
    assert attr == 'STUB'


def test_wrap_errors_compat():
    "Legacy decorator signature. TODO: remove in 1.0"

    @argh.wrap_errors(KeyError, ValueError, TypeError)
    def func():
        pass

    attr = getattr(func, argh.constants.ATTR_WRAPPED_EXCEPTIONS)
    assert attr == [KeyError, ValueError, TypeError]


def test_expects_obj():
    @argh.expects_obj
    def func(args):
        pass

    attr = getattr(func, argh.constants.ATTR_EXPECTS_NAMESPACE_OBJECT)
    assert attr == True
