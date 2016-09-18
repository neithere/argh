# coding: utf-8
"""
Unit Tests For Decorators
~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import pytest

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


def test_expects_obj():
    @argh.expects_obj
    def func(args):
        pass

    attr = getattr(func, argh.constants.ATTR_EXPECTS_NAMESPACE_OBJECT)
    assert attr is True


def test_parse_sphinx_params():
    @argh.parse_docstring
    def func(foo):
        '''
        This is the description
        :param foo: enable frobulation?
        :type foo: bool
        :return: bar
        '''

    attrs = getattr(func, argh.constants.ATTR_ARGS)
    assert attrs == [
        dict(option_strings=('foo',), help='enable frobulation?'),
    ]
    # TODO: assert that the func help msg is just "This is the description"


def test_parse_sphinx_docstring_from_class():
    class Fooer():
        @argh.parse_docstring
        def func(foo):
            '''
            This is the description
            :param foo: enable frobulation?
            '''

    attrs = getattr(Fooer.func, argh.constants.ATTR_ARGS)
    assert attrs == [
        dict(option_strings=('foo',), help='enable frobulation?'),
    ]


def test_parse_sphinx_docstring_overriden_by_arg_defn():
    @argh.parse_docstring
    @argh.arg('bar', help='help text')
    def func(foo, bar):
        '''
        This is the description
        :param foo: enable frobulation?
        :type foo: bool
        :param bar: overriden help text
        :return: bar
        '''

    attrs = getattr(func, argh.constants.ATTR_ARGS)
    assert attrs == [
        dict(option_strings=('bar',), help='help text'),
        dict(option_strings=('foo',), help='enable frobulation?'),
    ]


@pytest.mark.skip('''not sure what do to do here. I think an arg definition should always override
             the docstring personally. Or perhaps they could be intelligently merged?''')
def test_parse_sphinx_arg_defn_overridden_by_docstring():
    @argh.arg('bar', help='help text')
    @argh.parse_docstring
    def func(foo, bar):
        '''
        This is the description
        :param foo: enable frobulation?
        :type foo: bool
        :param bar: overriden help text
        :return: bar
        '''

    attrs = getattr(func, argh.constants.ATTR_ARGS)
    assert attrs == [
        dict(option_strings=('bar',), help='help text'),
        dict(option_strings=('foo',), help='enable frobulation?'),
    ]
