#
#  Copyright © 2010—2023 Andrey Mikhaylenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README.rst for copying conditions.
#
"""
Assembling
~~~~~~~~~~

Functions and classes to properly assemble your commands in a parser.
"""
import inspect
from argparse import ZERO_OR_MORE, ArgumentParser
from collections import OrderedDict
from dataclasses import asdict
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Type, Union

from argh.completion import COMPLETION_ENABLED
from argh.constants import (
    ATTR_ALIASES,
    ATTR_ARGS,
    ATTR_EXPECTS_NAMESPACE_OBJECT,
    ATTR_NAME,
    DEFAULT_ARGUMENT_TEMPLATE,
    DEST_FUNCTION,
    PARSER_FORMATTER,
)
from argh.dto import NotDefined, ParserAddArgumentSpec
from argh.exceptions import AssemblingError
from argh.utils import get_arg_spec, get_subparsers

__all__ = [
    "set_default_command",
    "add_commands",
    "add_subcommands",
]


def extract_parser_add_argument_kw_from_signature(
    function: Callable,
) -> Iterator[ParserAddArgumentSpec]:
    if getattr(function, ATTR_EXPECTS_NAMESPACE_OBJECT, False):
        return

    func_spec = get_arg_spec(function)

    defaults: Dict[str, Any] = dict(
        zip(reversed(func_spec.args), reversed(func_spec.defaults or tuple()))
    )
    defaults.update(getattr(func_spec, "kwonlydefaults", None) or {})

    kwonly = getattr(func_spec, "kwonlyargs", [])

    # define the list of conflicting option strings
    # (short forms, i.e. single-character ones)
    named_args = set(list(defaults) + kwonly)
    named_arg_chars = [a[0] for a in named_args]
    named_arg_char_counts = dict(
        (char, named_arg_chars.count(char)) for char in set(named_arg_chars)
    )
    conflicting_opts = tuple(
        char for char in named_arg_char_counts if 1 < named_arg_char_counts[char]
    )

    for name in func_spec.args + kwonly:
        cli_arg_names: List[str] = []
        akwargs: Dict[str, Any] = {}  # keyword arguments for add_argument()
        is_required: Union[bool, Type[NotDefined]] = NotDefined
        default_value: Any = NotDefined

        if name in defaults or name in kwonly:
            if name in defaults:
                default_value = defaults.get(name)
            else:
                is_required = True
            cli_arg_names = [f"-{name[0]}", f"--{name}"]
            if name.startswith(conflicting_opts):
                # remove short name
                cli_arg_names = cli_arg_names[1:]

        else:
            # positional argument
            cli_arg_names = [name]

        # cmd(foo_bar)  ->  add_argument("foo-bar")
        cli_arg_names = [
            x.replace("_", "-") if x.startswith("-") else x for x in cli_arg_names
        ]

        spec = ParserAddArgumentSpec(
            name,
            cli_arg_names,
            default_value=default_value,
            other_add_parser_kwargs=akwargs,
        )
        if is_required != NotDefined:
            spec.is_required = is_required
        yield spec

    if func_spec.varargs:
        # *args
        yield ParserAddArgumentSpec(
            func_spec.varargs,
            [func_spec.varargs],
            nargs=ZERO_OR_MORE,
        )


def guess_extra_parser_add_argument_spec_kwargs(
    parser_add_argument_spec: ParserAddArgumentSpec,
) -> Dict[str, Any]:
    """
    Given an argument specification, returns types, actions, etc. that could be
    guessed from it:

    * ``default=3`` → ``type=int``

      TODO: deprecate in favour of ``foo: int = 3`` in func signature.

    * ``choices=[3]`` → ``type=int``

      TODO: deprecate in favour of ``foo: int`` in func signature.

    * ``type=bool`` → ``action="store_false"`` or ``action="store_true"``
      (if action was not explicitly defined).

    """
    other_add_parser_kwargs = parser_add_argument_spec.other_add_parser_kwargs
    guessed: Dict[str, Any] = {}

    # Parser actions that accept argument 'type'
    TYPE_AWARE_ACTIONS = "store", "append"

    # guess type/action from default value
    default_value = parser_add_argument_spec.default_value
    if default_value not in (None, NotDefined):
        if isinstance(default_value, bool):
            if other_add_parser_kwargs.get("action") is None:
                # infer action from default value
                guessed["action"] = "store_false" if default_value else "store_true"
        elif other_add_parser_kwargs.get("type") is None:
            # infer type from default value
            # (make sure that action handler supports this keyword)
            if other_add_parser_kwargs.get("action", "store") in TYPE_AWARE_ACTIONS:
                guessed["type"] = type(default_value)

    # guess type from choices (first item)
    if other_add_parser_kwargs.get("choices") and "type" not in list(guessed) + list(
        other_add_parser_kwargs
    ):
        guessed["type"] = type(other_add_parser_kwargs["choices"][0])

    return guessed


def set_default_command(parser, function: Callable) -> None:
    """
    Sets default command (i.e. a function) for given parser.

    If `parser.description` is empty and the function has a docstring,
    it is used as the description.

    .. note::

       If there are both explicitly declared arguments (e.g. via
       :func:`~argh.decorators.arg`) and ones inferred from the function
       signature, declared ones will be merged into inferred ones.
       If an argument does not conform to the function signature,
       `AssemblingError` is raised.

    .. note::

       If the parser was created with ``add_help=True`` (which is by default),
       option name ``-h`` is silently removed from any argument.

    """
    func_spec = get_arg_spec(function)
    has_varkw = bool(func_spec.varkw)  # the **kwargs thing

    declared_args: List[ParserAddArgumentSpec] = getattr(function, ATTR_ARGS, [])
    inferred_args: List[ParserAddArgumentSpec] = list(
        extract_parser_add_argument_kw_from_signature(function)
    )

    if declared_args and not inferred_args and not has_varkw:
        # XXX breaking change, new behaviour
        raise AssemblingError(
            f"{function.__name__}: cannot extend argument declarations "
            "for an endpoint function that takes no arguments."
        )

    if not declared_args:
        parser_add_argument_specs = inferred_args
    else:
        # We've got a mixture of declared and inferred arguments
        try:
            parser_add_argument_specs = _merge_inferred_and_declared_args(
                inferred_args=inferred_args,
                declared_args=declared_args,
                has_varkw=has_varkw,
                parser=parser,
            )
        except AssemblingError as exc:
            print(exc)
            raise AssemblingError(f"{function.__name__}: {exc}") from exc

    # add the fully formed argument specs to the parser
    for orig_spec in parser_add_argument_specs:
        spec = _prepare_parser_add_argument_spec(
            parser_add_argument_spec=orig_spec, parser_adds_help_arg=parser.add_help
        )

        try:
            action = parser.add_argument(
                *spec.cli_arg_names,
                **spec.get_all_kwargs(),
            )
        except Exception as exc:
            err_cli_args = "/".join(spec.cli_arg_names)
            raise AssemblingError(
                f"{function.__name__}: cannot add '{spec.func_arg_name}' as {err_cli_args}: {exc}"
            ) from exc

        if COMPLETION_ENABLED and spec.completer:
            action.completer = spec.completer

    # display endpoint function docstring in command help
    docstring = inspect.getdoc(function)
    if docstring and not parser.description:
        parser.description = docstring

    # add the endpoint function to the parsing result (namespace)
    parser.set_defaults(
        **{
            DEST_FUNCTION: function,
        }
    )


def _prepare_parser_add_argument_spec(
    parser_add_argument_spec: ParserAddArgumentSpec, parser_adds_help_arg: bool
) -> ParserAddArgumentSpec:
    # deep copy
    spec = ParserAddArgumentSpec(**asdict(parser_add_argument_spec))

    # add types, actions, etc. (e.g. default=3 implies type=int)
    spec.other_add_parser_kwargs.update(
        guess_extra_parser_add_argument_spec_kwargs(spec)
    )

    # display default value for this argument in command help
    if "help" not in spec.other_add_parser_kwargs:
        spec.other_add_parser_kwargs.update(help=DEFAULT_ARGUMENT_TEMPLATE)

    # If the parser was created with `add_help=True`, it automatically adds
    # the -h/--help argument (on argparse side).  If we have added -h for
    # another argument (e.g. --host) earlier (inferred or declared), we
    # need to remove that short form now.
    if parser_adds_help_arg and "-h" in spec.cli_arg_names:
        spec.cli_arg_names = [name for name in spec.cli_arg_names if name != "-h"]

    return spec


def _merge_inferred_and_declared_args(
    inferred_args: List[ParserAddArgumentSpec],
    declared_args: List[ParserAddArgumentSpec],
    parser: ArgumentParser,
    has_varkw: bool,
) -> List[ParserAddArgumentSpec]:
    # a mapping of "dest" strings to argument declarations.
    #
    # * a "dest" string is a normalized form of argument name, i.e.:
    #
    #     "-f", "--foo" → "foo"
    #     "foo-bar"     → "foo_bar"
    #
    # * argument declaration is a dictionary representing an argument;
    #   it is obtained either from extract_parser_add_argument_kw_from_signature()
    #   or from an @arg decorator (as is).
    #
    specs_by_func_arg_name = OrderedDict()

    # arguments inferred from function signature
    for parser_add_argument_spec in inferred_args:
        # dest = _get_parser_param_kwargs(parser, argspec)["dest"]
        specs_by_func_arg_name[
            parser_add_argument_spec.func_arg_name
        ] = parser_add_argument_spec

    # arguments declared via @arg decorator
    for declared_spec in declared_args:
        func_arg_name = parser_add_argument_spec.func_arg_name

        if func_arg_name in specs_by_func_arg_name:
            # the argument is already known from function signature
            #
            # now make sure that this declared arg conforms to the function
            # signature and therefore only refines an inferred arg:
            #
            #      @arg("my-foo")    maps to  func(my_foo)
            #      @arg("--my-bar")  maps to  func(my_bar=...)

            # either both arguments are positional or both are optional
            decl_positional = _is_positional(declared_spec.cli_arg_names)
            infr_positional = _is_positional(
                specs_by_func_arg_name[func_arg_name].cli_arg_names
            )
            if decl_positional != infr_positional:
                kinds = {True: "positional", False: "optional"}
                kind_inferred = kinds[infr_positional]
                kind_declared = kinds[decl_positional]
                raise AssemblingError(
                    f'argument "{func_arg_name}" declared as {kind_inferred} '
                    f"(in function signature) and {kind_declared} (via decorator)"
                )

            # merge explicit argument declaration into the inferred one
            # (e.g. `help=...`)
            specs_by_func_arg_name[func_arg_name].update(parser_add_argument_spec)
        else:
            # the argument is not in function signature
            if has_varkw:
                # function accepts **kwargs; the argument goes into it
                specs_by_func_arg_name[func_arg_name] = parser_add_argument_spec
            else:
                # there's no way we can map the argument declaration
                # to function signature
                dest_option_strings = (
                    specs_by_func_arg_name[x].cli_arg_names
                    for x in specs_by_func_arg_name
                )
                msg_flags = ", ".join(declared_spec.cli_arg_names)
                msg_signature = ", ".join("/".join(x) for x in dest_option_strings)
                raise AssemblingError(
                    f"argument {msg_flags} does not fit "
                    f"function signature: {msg_signature}"
                )

    # pack the modified data back into a list
    return list(specs_by_func_arg_name.values())


def _get_dest(parser: ArgumentParser, argspec: Dict[str, Any]) -> str:
    """
    Given a dict representing the keywords to `parser.add_argument()`, extract
    and normalise the option name::

        >>> _get_dest(parser, {"option_strings": ("-f", "--foo-bar", "--whatever")})
        "foo_bar"

    """
    kwargs = _get_parser_param_kwargs(parser, argspec)
    return kwargs["dest"]


def _get_parser_param_kwargs(
    parser: ArgumentParser, argspec: Dict[str, Any]
) -> Dict[str, Any]:
    "TODO: explain"
    argspec = argspec.copy()  # parser methods modify source data
    args = argspec.pop("option_strings")

    # These two protected methods return something that is, frankly, not very useful:
    #
    # >>> p._get_positional_kwargs('foo-bar')
    # {'required': True, 'dest': 'foo-bar', 'option_strings': []}
    #
    # >>> p._get_optional_kwargs('foo-bar')
    # Traceback (most recent call last):
    #   File "<stdin>", line 1, in <module>
    #   File "/usr/lib64/python3.11/argparse.py", line 1571, in _get_optional_kwargs
    #     raise ValueError(msg % args)
    # ValueError: invalid option string 'foo-bar': must start with a character '-'
    #
    # >>> p._get_positional_kwargs('--foo-bar')
    # {'required': True, 'dest': '--foo-bar', 'option_strings': []}
    #
    # >>> p._get_optional_kwargs('--foo-bar')
    # {'dest': 'foo_bar', 'option_strings': ['--foo-bar']}
    #
    # >>> p._get_optional_kwargs('-a', '-b', '--c', '--d')
    # {'dest': 'c', 'option_strings': ['-a', '-b', '-c', '-d']}
    #
    # Get rid of this.  Use function signature as the source of truth.
    # (**kwargs allows arbitrary args too.)
    # If all are options (`-*`), pick the first elem with `--` (if any) or with `-`,
    # strip the prefix and normalise `-` to `_`.
    # That's all this thing does,
    if _is_positional(args, prefix_chars=parser.prefix_chars):
        get_kwargs = parser._get_positional_kwargs
    else:
        get_kwargs = parser._get_optional_kwargs

    kwargs = get_kwargs(*args, **argspec)

    kwargs["dest"] = kwargs["dest"].replace("-", "_")

    return kwargs


def _is_positional(args: List[str], prefix_chars: str = "-") -> bool:
    if not args or not args[0]:
        raise ValueError("Expected at least one argument")
    if args[0][0].startswith(tuple(prefix_chars)):
        return False
    return True


def add_commands(
    parser: ArgumentParser,
    functions: List[Callable],
    group_name: Optional[str] = None,
    group_kwargs: Optional[Dict[str, Any]] = None,
    func_kwargs: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Adds given functions as commands to given parser.

    :param parser:

        an :class:`argparse.ArgumentParser` instance.

    :param functions:

        a list of functions. A subparser is created for each of them.
        If the function is decorated with :func:`~argh.decorators.arg`, the
        arguments are passed to :meth:`argparse.ArgumentParser.add_argument`.
        See also :func:`~argh.dispatching.dispatch` for requirements
        concerning function signatures. The command name is inferred from the
        function name. Note that the underscores in the name are replaced with
        hyphens, i.e. function name "foo_bar" becomes command name "foo-bar".

    :param group_name:

        an optional string representing the group of commands. For example, if
        a command named "hello" is added without the group name, it will be
        available as "prog.py hello"; if the group name if specified as "greet",
        then the command will be accessible as "prog.py greet hello". The
        group itself is not callable, so "prog.py greet" will fail and only
        display a help message.

    :param func_kwargs:

        a `dict` of keyword arguments to be passed to each nested ArgumentParser
        instance created per command (i.e. per function).  Members of this
        dictionary have the highest priority, so a function's docstring is
        overridden by a `help` in `func_kwargs` (if present).

    :param group_kwargs:

        a `dict` of keyword arguments to be passed to the nested ArgumentParser
        instance under given `group_name`.

    .. note::

        This function modifies the parser object. Generally side effects are
        bad practice but we don't seem to have any choice as ArgumentParser is
        pretty opaque.
        You may prefer :meth:`~argh.helpers.ArghParser.add_commands` for a bit
        more predictable API.

    .. note::

       An attempt to add commands to a parser which already has a default
       function (e.g. added with :func:`~argh.assembling.set_default_command`)
       results in `AssemblingError`.

    """
    group_kwargs = group_kwargs or {}

    subparsers_action = get_subparsers(parser, create=True)

    if group_name:
        # Make a nested parser and init a deeper _SubParsersAction under it.

        # Create a named group of commands.  It will be listed along with
        # root-level commands in ``app.py --help``; in that context its `title`
        # can be used as a short description on the right side of its name.
        # Normally `title` is shown above the list of commands
        # in ``app.py my-group --help``.
        subsubparser = subparsers_action.add_parser(
            group_name, help=group_kwargs.get("title")
        )
        subparsers_action = subsubparser.add_subparsers(**group_kwargs)
    else:
        if group_kwargs:
            raise ValueError("`group_kwargs` only makes sense with `group_name`.")

    for func in functions:
        cmd_name, func_parser_kwargs = _extract_command_meta_from_func(func)

        # override any computed kwargs by manually supplied ones
        if func_kwargs:
            func_parser_kwargs.update(func_kwargs)

        # create and set up the parser for this command
        command_parser = subparsers_action.add_parser(cmd_name, **func_parser_kwargs)
        set_default_command(command_parser, func)


def _extract_command_meta_from_func(func: Callable) -> Tuple[str, dict]:
    # use explicitly defined name; if none, use function name (a_b → a-b)
    cmd_name = getattr(func, ATTR_NAME, func.__name__.replace("_", "-"))

    func_parser_kwargs: Dict[str, Any] = {
        # add command help from function's docstring
        "help": func.__doc__,
        # set default formatter
        "formatter_class": PARSER_FORMATTER,
    }

    # add aliases for command name
    func_parser_kwargs["aliases"] = getattr(func, ATTR_ALIASES, [])

    return cmd_name, func_parser_kwargs


def add_subcommands(
    parser: ArgumentParser, group_name: str, functions: List[Callable], **group_kwargs
) -> None:
    """
    A wrapper for :func:`add_commands`.

    These examples are equivalent::

        add_commands(parser, [get, put], group_name="db",
                     group_kwargs={
                         "title": "database commands",
                         "help": "CRUD for our silly database"
                     })

        add_subcommands(parser, "db", [get, put],
                        title="database commands",
                        help="CRUD for our database")

    """
    add_commands(parser, functions, group_name=group_name, group_kwargs=group_kwargs)
