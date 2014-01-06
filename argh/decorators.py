# coding: utf-8
#
#  Copyright © 2010—2014 Andrey Mikhaylenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README.rst for copying conditions.
#
"""
Command decorators
~~~~~~~~~~~~~~~~~~
"""
from argh.assembling import _fix_compat_issue29
from argh.constants import (ATTR_ALIASES, ATTR_ARGS, ATTR_NAME,
                            ATTR_WRAPPED_EXCEPTIONS,
                            ATTR_WRAPPED_EXCEPTIONS_PROCESSOR,
                            ATTR_INFER_ARGS_FROM_SIGNATURE,
                            ATTR_EXPECTS_NAMESPACE_OBJECT)


__all__ = ['alias', 'aliases', 'named', 'arg', 'plain_signature', 'command',
           'wrap_errors', 'expects_obj']


def named(new_name):
    """
    Sets given string as command name instead of the function name.
    The string is used verbatim without further processing.

    Usage::

        @named('load')
        def do_load_some_stuff_and_keep_the_original_function_name(args):
            ...

    The resulting command will be available only as ``load``.  To add aliases
    without renaming the command, check :func:`aliases`.

    .. versionadded:: 0.19
    """
    def wrapper(func):
        setattr(func, ATTR_NAME, new_name)
        return func
    return wrapper


def alias(new_name):  # pragma: nocover
    """
    .. deprecated:: 0.19

       Use :func:`named` or :func:`aliases` instead.
    """
    import warnings
    warnings.warn('Decorator @alias() is deprecated. '
                  'Use @aliases() or @named() instead.', DeprecationWarning)
    def wrapper(func):
        setattr(func, ATTR_NAME, new_name)
        _fix_compat_issue29(func)
        return func
    return wrapper


def aliases(*names):
    """
    Defines alternative command name(s) for given function (along with its
    original name). Usage::

        @aliases('co', 'check')
        def checkout(args):
            ...

    The resulting command will be available as ``checkout``, ``check`` and ``co``.

    .. note::

       This decorator only works with a recent version of argparse (see `Python
       issue 9324`_ and `Python rev 4c0426`_).  Such version ships with
       **Python 3.2+** and may be available in other environments as a separate
       package.  Argh does not issue warnings and simply ignores aliases if
       they are not supported.  See :attr:`~argh.assembling.SUPPORTS_ALIASES`.

       .. _Python issue 9324: http://bugs.python.org/issue9324
       .. _Python rev 4c0426: http://hg.python.org/cpython/rev/4c0426261148/

    .. versionadded:: 0.19
    """
    def wrapper(func):
        setattr(func, ATTR_ALIASES, names)
        return func
    return wrapper


def plain_signature(func):  # pragma: nocover
    """
    .. deprecated:: 0.20

       Function signature is now introspected by default.
       Use :func:`expects_obj` for inverted behaviour.
    """
    import warnings
    warnings.warn('Decorator @plain_signature is deprecated. '
                  'Function signature is now introspected by default.',
                  DeprecationWarning)
    return func


def arg(*args, **kwargs):
    """
    Declares an argument for given function. Does not register the function
    anywhere, nor does it modify the function in any way. The signature is
    exactly the same as that of :meth:`argparse.ArgumentParser.add_argument`,
    only some keywords are not required if they can be easily guessed.

    Usage::

        @arg('path')
        @arg('--format', choices=['yaml','json'], default='json')
        @arg('--dry-run', default=False)
        @arg('-v', '--verbosity', choices=range(0,3), default=1)
        def load(args):
            loaders = {'json': json.load, 'yaml': yaml.load}
            loader = loaders[args.format]
            data = loader(args.path)
            if not args.dry_run:
                if 1 < verbosity:
                    print('saving to the database')
                put_to_database(data)

    Note that:

    * you didn't have to specify ``action="store_true"`` for ``--dry-run``;
    * you didn't have to specify ``type=int`` for ``--verbosity``.

    """
    def wrapper(func):
        declared_args = getattr(func, ATTR_ARGS, [])
        # The innermost decorator is called first but appears last in the code.
        # We need to preserve the expected order of positional arguments, so
        # the outermost decorator inserts its value before the innermost's:
        declared_args.insert(0, dict(option_strings=args, **kwargs))
        setattr(func, ATTR_ARGS, declared_args)
        _fix_compat_issue29(func)
        return func
    return wrapper


def command(func):
    """
    .. deprecated:: 0.21

       Function signature is now introspected by default.
       Use :func:`expects_obj` for inverted behaviour.
    """
    import warnings
    warnings.warn('Decorator @command is deprecated. '
                  'Function signature is now introspected by default.',
                  DeprecationWarning)
    setattr(func, ATTR_INFER_ARGS_FROM_SIGNATURE, True)
    return func


def _fix_compat_issue36(func, errors, processor, args):
    #
    # TODO: remove before 1.0 release (will break backwards compatibility)
    #

    if errors and not hasattr(errors, '__iter__'):
        # what was expected to be a list is actually its first item
        errors = [errors]

        # what was expected to be a function is actually the second item
        if processor:
            errors.append(processor)
            processor = None

        # *args, if any, are the remaining items
        if args:
            errors.extend(args)

        import warnings
        warnings.warn('{func.__name__}: wrappable exceptions must be declared '
                      'as list, i.e. @wrap_errors([{errors}]) instead of '
                      '@wrap_errors({errors})'.format(
                        func=func, errors=', '.join(x.__name__ for x in errors)),
                      DeprecationWarning)

    return errors, processor


def wrap_errors(errors=None, processor=None, *args):
    """
    Decorator. Wraps given exceptions into
    :class:`~argh.exceptions.CommandError`. Usage::

        @wrap_errors([AssertionError])
        def foo(x=None, y=None):
            assert x or y, 'x or y must be specified'

    If the assertion fails, its message will be correctly printed and the
    stack hidden. This helps to avoid boilerplate code.

    :param errors:
        A list of exception classes to catch.
    :param processor:
        A callable that expects the exception object and returns a string.
        For example, this renders all wrapped errors in red colour::

            from termcolor import colored

            def failure(err):
                return colored(str(err), 'red')

            @wrap_errors(processor=failure)
            def my_command(...):
                ...

    .. warning::

       The `exceptions` argument **must** be a list.

       For backward compatibility reasons the old way is still allowed::

           @wrap_errors(KeyError, ValueError)

       However, the hack that allows that will be **removed** in Argh 1.0.

       Please make sure to update your code.

    """

    def wrapper(func):
        errors_, processor_ = _fix_compat_issue36(func, errors, processor, args)

        if errors_:
            setattr(func, ATTR_WRAPPED_EXCEPTIONS, errors_)

        if processor_:
            setattr(func, ATTR_WRAPPED_EXCEPTIONS_PROCESSOR, processor_)

        return func
    return wrapper


def expects_obj(func):
    """
    Marks given function as expecting a namespace object.

    Usage::

        @arg('bar')
        @arg('--quux', default=123)
        @expects_obj
        def foo(args):
            yield args.bar, args.quux

    This is equivalent to::

        def foo(bar, quux=123):
            yield bar, quux

    In most cases you don't need this decorator.
    """
    setattr(func, ATTR_EXPECTS_NAMESPACE_OBJECT, True)
    return func
