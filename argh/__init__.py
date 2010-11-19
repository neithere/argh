# -*- coding: utf-8 -*-
"""
API reference
=============

"""
__all__ = (
    'add_commands', 'alias', 'arg', 'ArghParser', 'CommandError', 'confirm',
    'dispatch', 'generator', 'plain_signature'
)

import locale
import sys
from functools import wraps
import argparse


class CommandError(Exception):
    """The only exception that is wrapped by the dispatcher. Useful for
    print-and-exit tasks. The following examples are equal::

        @arg('key')
        def foo(args):
            try:
                db[args.key]
            except KeyError as e:
                print(u'Could not fetch item: {0}'.format(e))
                return

        @arg('key')
         def bar(args):
            try:
                db[args.key]
            except KeyError as e:
                raise CommandError(u'Could not fetch item: {0}'.format(e))

    This exception can be safely used in both printing and :func:`generator
    <generating>` commands.
    """


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
    """Marks given function as a generator. Such function will be called by
    :func:`dispatch <dispatcher>` and the yielded strings printed one by one.

    Encoding of the output is automatically adapted to the terminal or a pipe.

    Functions without this decorator are expected to simply print their output.

    These three commands produce equal results::

        def foo(args):
            print('hello')
            print('world')

        @generator
        def bar(args):
            return ['hello', 'world']

        @generator
        def quux(args):
            yield('hello')
            yield('world')

    """
    func.argh_generator = True
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
        func.argh_args.append((args, kwargs))
        return func
    return wrapper

def _get_subparsers(parser):
    """Returns the :class:`argparse._SupParsersAction` instance for given
    :class:`ArgumentParser` instance as would have been returned by
    :meth:`ArgumentParser.add_subparsers`. The problem with the latter is that
    it only works once and raises an exception on the second attempt, and the
    public API seems to lack a method to get *existing* subparsers.
    """
    # note that ArgumentParser._subparsers is *not* what is returned by
    # ArgumentParser.add_subparsers().
    if parser._subparsers:
        actions = [a for a in parser._actions
                   if isinstance(a, argparse._SubParsersAction)]
        assert len(actions) == 1
        return actions[0]
    else:
        return parser.add_subparsers()

def add_commands(parser, functions, namespace=None, title=None,
                 description=None, help=None):
    """Adds given functions as commands to given parser.

    :param parser:

        an :class:`argparse.ArgumentParser` instance.

    :param functions:

        a list of functions. A subparser is created for each of them. If the
        function is decorated with :func:`arg`, the arguments are passed to
        the :class:`~argparse.ArgumentParser.add_argument` method of the
        parser. See also :func:`dispatch` for requirements concerning function
        signatures. The command name is inferred from the function name. Note
        that the underscores in the name are replaced with hyphens, i.e.
        function name "foo_bar" becomes command name "foo-bar".

    :param namespace:

        an optional string representing the group of commands. For example, if
        a command named "hello" is added without the namespace, it will be
        available as "prog.py hello"; if the namespace if specified as "greet",
        then the command will be accessible as "prog.py greet hello". The
        namespace itself is not callable, so "prog.py greet" will fail and only
        display a help message.

    Help message for a namespace can be also tuned with these params (provided
    that you specify the `namespace`):

    :param title:

        passed to :meth:`argsparse.ArgumentParser.add_subparsers` as `title`.

    :param description:

        passed to :meth:`argsparse.ArgumentParser.add_subparsers` as
        `description`.

    :param help:

        passed to :meth:`argsparse.ArgumentParser.add_subparsers` as `help`.

    .. note::

        This function modifies the parser object. Generally side effects are
        bad practice but we don't seem to have any choice as ArgumentParser is
        pretty opaque. You may prefer :class:`ArghParser.add_commands` for a
        bit more predictable API.

    .. admonition:: Design flaw

        This function peeks into the parser object using its internal API.
        Unfortunately the public API does not allow to *get* the subparsers, it
        only lets you *add* them, and do that *once*. So you would have to toss
        the subparsers object around to add something later. That said, I doubt
        that argparse will change a lot in the future as it's already pretty
        stable. If some implementation details would change and break `argh`,
        we'll simply add a workaround a keep it compatibile.

    """
    subparsers = _get_subparsers(parser)

    if namespace:
        # make a namespace placeholder and register the commands within it
        assert isinstance(namespace, str)
        subsubparser = subparsers.add_parser(namespace)
        subparsers = subsubparser.add_subparsers(title=title,
                                                description=description,
                                                help=help)
    else:
        assert not any([title, description, help]), (
            'Arguments "title", "description" or "extra_help" only make sense '
            'if provided along with a namespace.')

    for func in functions:
        # XXX we could add multiple aliases here but it's a bit of a hack
        cmd_name = getattr(func, 'argh_alias', func.__name__.replace('_','-'))
        cmd_help = func.__doc__
        command_parser = subparsers.add_parser(cmd_name, help=cmd_help)
        for a_args, a_kwargs in getattr(func, 'argh_args', []):
            command_parser.add_argument(*a_args, **a_kwargs)
        command_parser.set_defaults(function=func)

def dispatch(parser, argv=None, add_help_command=True, encoding=None,
             intercept=False):
    """Parses given list of arguments using given parser, calls the relevant
    function and prints the result.

    The target function should expect one positional argument: the
    :class:`argparse.Namespace` object. However, if the function is decorated with
    :func:`plain_signature`, the positional and named arguments from the
    namespace object are passed to the function instead of the object itself.

    :param parser:
        the ArgumentParser instance.
    :param argv:
        a list of strings representing the arguments. If `None`, ``sys.argv``
        is used instead. Default is `None`.
    :param add_help_command:
        if `True`, converts first positional argument "help" to a keyword
        argument so that ``help foo`` becomes ``foo --help`` and displays usage
        information for "foo". Default is `True`.

    Exceptions are not wrapped and will propagate. The only exception among the
    exceptions is :class:`CommandError` which is interpreted as an expected
    event so the traceback is hidden.
    """
    if argv is None:
        argv = sys.argv[1:]
    if add_help_command:
        if argv and argv[0] == 'help':
            argv.pop(0)
            argv.append('--help')

    # this will raise SystemExit if parsing fails
    args = parser.parse_args(argv)

    # try different ways of calling the command; if meanwhile it raises
    # CommandError, return the string representation of that error
    try:
        if getattr(args.function, 'argh_no_namespace', False):
            # filter the namespace variables so that only those expected by the
            # actual function will pass
            f = args.function
            expected_args = f.func_code.co_varnames[:f.func_code.co_argcount]
            ok_args = [x for x in args._get_args() if x in expected_args]
            ok_kwargs = dict((k,v) for k,v in args._get_kwargs()
                             if k in expected_args)
            result = args.function(*ok_args, **ok_kwargs)
        else:
            result = args.function(args)
        if getattr(args.function, 'argh_generator', False):
            # handle iterable results (function marked with @generator decorator)
            if not encoding:
                # choose between terminal's and system's preferred encodings
                if sys.stdout.isatty():
                    encoding = sys.stdout.encoding
                else:
                    encoding = locale.getpreferredencoding()
            if intercept:
                return '\n'.join([line.encode(encoding) for line in result])
            else:
                # we must print each line as soon as it is generated to ensure that
                # it is displayed to the user before anything else happens, e.g.
                # raw_input() is called
                for line in result:
                    print(line.encode(encoding))
        else:
            return result
    except CommandError as e:
        if intercept:
            return str(e)
        else:
            print(e)


class ArghParser(argparse.ArgumentParser):
    """An :class:`ArgumentParser` suclass which adds a couple of convenience
    methods.

    There is actually no need to subclass the parser. The methods are but
    wrappers for stand-alone functions :func:`add_commands` and
    :func:`dispatch`.
    """
    def add_commands(self, *args, **kwargs):
        "Wrapper for :func:`add_commands`."
        return add_commands(self, *args, **kwargs)

    def dispatch(self, *args, **kwargs):
        "Wrapper for :func:`dispatch`."
        return dispatch(self, *args, **kwargs)


def confirm(action, default=None, skip=False):
    """A shortcut for typical confirmation prompt.

    :param action:
        a string describing the action, e.g. "Apply changes". A question mark
        will be appended.
    :param default:
        `bool` or `None`. Determines what happens when user hits :kbd:`Enter`
        without typing in a choice. If `True`, default choice is "yes". If
        `False`, it is "no". If `None` the prompt keeps reappearing until user
        types in a choice (not necessarily acceptable), Default is `None`.
    :param skip:
        `bool`l if `True`,

    Usage::

        @arg('key')
        @arg('-y', '--yes', help='do not prompt, always answer "yes"')
        def delete(args):
            item = db.get(Item, args.key)
            if confirm('Delete item {title}'.format(**item), skip=args.yes):
                item.delete()
                print('Item deleted.')
            else:
                print('Operation cancelled.')

    Returns `False` on `KeyboardInterrupt` event.
    """
    if skip:
        choice = 'y'
    else:
        defaults = {
            None: ('y','n'),
            True: ('Y','n'),
            False: ('y','N'),
        }
        y, n = defaults[default]
        prompt = u'{action}? ({y}/{n})'.format(**locals())
        choice = None
        try:
            if default is None:
                while not choice:
                    choice = raw_input(prompt)
            else:
                choice = raw_input(prompt) or ('y' if default else 'n')
        except KeyboardInterrupt:
            return False
    return choice in ('y', 'yes')
