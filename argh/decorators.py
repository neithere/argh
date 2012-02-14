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
==================
"""
import inspect

from argh.constants import ATTR_ALIAS, ATTR_ARGS, ATTR_NO_NAMESPACE


__all__ = ['alias', 'arg', 'command', 'plain_signature']


def alias(name):
    """Defines the command name for given function. The alias will be used for
    the command instead of the original function name.

    .. note::

        Currently `argparse` does not support (multiple) aliases so this
        decorator actually *renames* the command. However, in the future it may
        accept multiple names for the same command.

    """
    def wrapper(func):
        setattr(func, ATTR_ALIAS, name)
        return func
    return wrapper

def generator(func):  # pragma: no cover
    """
    .. warning::

        This decorator is deprecated. Argh can detect whether the result is a
        generator without explicit decorators.

    """
    import warnings
    warnings.warn('Decorator @generator is deprecated. The commands can still '
                  'return generators.', DeprecationWarning)
    return func

def plain_signature(func):
    """Marks that given function expects ordinary positional and named
    arguments instead of a single positional argument (a
    :class:`argparse.Namespace` object). Useful for existing functions that you
    don't want to alter nor write wrappers by hand. Usage::

        @arg('filename')
        @plain_signature
        def load(filename):
            print json.load(filename)

    ...is equivalent to::

        @argh('filename')
        def load(args):
            print json.load(args.filename)

    Whether to use the decorator is mostly a matter of taste. Without it the
    function declaration is more :term:`DRY`. However, it's a pure time saver
    when it comes to exposing a whole lot of existing :term:`CLI`-agnostic code
    as a set of commands. You don't need to rename each and every agrument all
    over the place; instead, you just stick this and some :func:`arg`
    decorators on top of every function and that's it.
    """
    setattr(func, ATTR_NO_NAMESPACE, True)
    return func

def arg(*args, **kwargs):
    """Declares an argument for given function. Does not register the function
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
    kwargs = kwargs.copy()

    # try guessing some stuff
    if kwargs.get('choices') and not 'type' in kwargs:
        kwargs['type'] = type(kwargs['choices'][0])
    if 'default' in kwargs and not 'action' in kwargs:
        value = kwargs['default']
        if isinstance(value, bool):
            # infer action from default value
            kwargs['action'] = 'store_false' if value else 'store_true'
        elif 'type' not in kwargs and value is not None:
            # infer type from default value
            kwargs['type'] = type(value)

    def wrapper(func):
        declared_args = getattr(func, ATTR_ARGS, [])
        # The innermost decorator is called first but appears last in the code.
        # We need to preserve the expected order of positional arguments, so
        # the outermost decorator inserts its value before the innermost's:
        declared_args.insert(0, (args, kwargs))
        setattr(func, ATTR_ARGS, declared_args)
        return func
    return wrapper

def command(func):
    """Infers argument specifications from given function. Wraps the function
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

    """
    # @plain_signature
    func = plain_signature(func)

    # @arg (inferred)
    spec = inspect.getargspec(func)
    kwargs = dict(zip(*[reversed(x) for x in (spec.args, spec.defaults or [])]))

    # define the list of conflicting option strings
    # (short forms, i.e. single-character ones)
    chars = [a[0] for a in spec.args]
    char_counts = dict((char, chars.count(char)) for char in set(chars))
    conflicting_opts = tuple(char for char in char_counts
                             if 1 < char_counts[char])

    for a in reversed(spec.args):  # @arg adds specs in reversed order
        if a in kwargs:
            if a.startswith(conflicting_opts):
                func = arg(
                    '--{0}'.format(a),
                    default=kwargs.get(a)
                )(func)
            else:
                func = arg(
                    '-{0}'.format(a[0]),
                    '--{0}'.format(a),
                    default=kwargs.get(a)
                )(func)
        else:
            func = arg(a)(func)

    return func
