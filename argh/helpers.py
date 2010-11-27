"""
Helpers
=======
"""
import argparse
import locale
import sys
from types import GeneratorType

from argh.exceptions import CommandError


__all__ = ['ArghParser', 'add_commands', 'dispatch', 'confirm']


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

    if not hasattr(args, 'function'):
        # FIXME: "./prog.py" hits this error while "./prog.py foo" doesn't
        # if there were no commands defined for the parser (a possible case)
        raise NotImplementedError('Cannot dispatch without commands')

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
        if isinstance(result, (GeneratorType, list, tuple)):
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
                    if not isinstance(line, unicode):
                        try:
                            line = unicode(line)
                        except UnicodeDecodeError:
                            line = str(line).decode('utf-8')
                    print(line.encode(encoding))
        else:
            return result
    except CommandError, e:
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
        types in a choice (not necessarily acceptable) or until the number of
        iteration reaches the limit. Default is `None`.
    :param skip:
        `bool`; if `True`, no interactive prompt is used and default choice is
        returned (useful for batch mode). Default is `False`.

    Usage::

        @arg('key')
        @arg('--silent', help='do not prompt, always give default answers')
        def delete(args):
            item = db.get(Item, args.key)
            if confirm('Delete '+item.title, default=True, skip=args.silent):
                item.delete()
                print('Item deleted.')
            else:
                print('Operation cancelled.')

    Returns `None` on `KeyboardInterrupt` event.
    """
    MAX_ITERATIONS = 3
    if skip:
        return default
    else:
        defaults = {
            None: ('y','n'),
            True: ('Y','n'),
            False: ('y','N'),
        }
        y, n = defaults[default]
        prompt = (u'%(action)s? (%(y)s/%(n)s)' % locals()).encode('utf-8')
        choice = None
        try:
            if default is None:
                cnt = 1
                while not choice and cnt < MAX_ITERATIONS:
                    choice = raw_input(prompt)
                    cnt += 1
            else:
                choice = raw_input(prompt)
        except KeyboardInterrupt:
            return None
    if choice in ('yes', 'y', 'Y'):
        return True
    if choice in ('no', 'n', 'N'):
        return False
    if default is not None:
        return default
    return None
