# -*- coding: utf-8 -*-
#
#  Copyright (c) 2010—2012 Andrey Mikhailenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README for copying conditions.
#
"""
Command decorators
~~~~~~~~~~~~~~~~~~
"""
from argh.constants import (ATTR_ALIASES, ATTR_ARGS, ATTR_NAME,
                            ATTR_NO_NAMESPACE, ATTR_WRAPPED_EXCEPTIONS,
                            ATTR_INFER_ARGS_FROM_SIGNATURE)
from argh.utils import Arg


__all__ = ['alias', 'aliases', 'named', 'arg', 'plain_signature', 'command',
           'wrap_errors']


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


def alias(new_name):
    """
    .. deprecated:: 0.19

       Use :func:`named` or :func:`aliases` instead.
    """
    import warnings
    warnings.warn('Decorator @alias() is deprecated. '
                  'Use @aliases() or @named() instead.', DeprecationWarning)
    return named(new_name)


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


def plain_signature(func):
    """
    .. deprecated:: 0.20

       Use :func:`command` instead.
    """
    import warnings
    warnings.warn('@plain_signature is deprecated, use @command instead',
                  DeprecationWarning)

    # cannot be replaced with ATTR_INFER_ARGS_FROM_SIGNATURE
    # until the latter allows merging explicit @arg declarations
    setattr(func, ATTR_NO_NAMESPACE, True)

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
        declared_args.insert(0, Arg(args, kwargs))
        setattr(func, ATTR_ARGS, declared_args)
        return func
    return wrapper


def command(func):
    """
    Infers argument specifications from given function. Wraps the function
    in the :func:`plain_signature` decorator and also in an :func:`arg`
    decorator for every actual argument the function expects.

    Usage::

        @command
        def foo(bar, quux=123):
            yield bar, quux

    This is equivalent to::

        @arg('-b', '--bar')
        @arg('-q', '--quux', default=123)
        def foo(args):
            yield args.bar, args.quux

    .. note::

       Python 3 supports annotations (:pep:`3107`). They can be used with Argh
       as help messages for arguments. These declarations are equivalent::

           @arg('--dry-run', help='do not modify the database', default=False)
           def save(args):
               ...

           @command
           def save(dry_run : 'do not modify the database' = False):
               ...


       Only strings are considered help messages.

    """
    setattr(func, ATTR_INFER_ARGS_FROM_SIGNATURE, True)
    return func


def wrap_errors(*exceptions):
    """
    Decorator. Wraps given exceptions into
    :class:`~argh.exceptions.CommandError`. Usage::

        @arg('-x')
        @arg('-y')
        @wrap_errors(AssertionError)
        def foo(args):
            assert args.x or args.y, 'x or y must be specified'

    If the assertion fails, its message will be correctly printed and the
    stack hidden. This helps to avoid boilerplate code.
    """
    def wrapper(func):
        setattr(func, ATTR_WRAPPED_EXCEPTIONS, exceptions)
        return func
    return wrapper
