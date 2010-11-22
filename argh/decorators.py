"""
Command decorators
==================
"""
from functools import wraps


__all__ = ['alias', 'plain_signature', 'arg']


def alias(name):
    """Defines the command name for given function. The alias will be used for
    the command instead of the original function name.

    .. note::

        Currently `argparse` does not support (multiple) aliases so this
        decorator actually *renames* the command. However, in the future it may
        accept multiple names for the same command.

    """
    def wrapper(func):
        func.argh_alias = name
        return func
    return wrapper

def generator(func):
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
    func.argh_no_namespace = True
    return func

def arg(*args, **kwargs):
    """Declares an argument for given function. Does not register the function
    anywhere, not does it modify the function in any way. The signature is
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
        func.argh_args = getattr(func, 'argh_args', [])
        # The innermost decorator is called first but appears last in the code.
        # We need to preserve the expected order of positional arguments, so
        # the outermost decorator inserts its value before the innermost's:
        func.argh_args.insert(0, (args, kwargs))
        return func
    return wrapper
