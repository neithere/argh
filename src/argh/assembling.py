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
import textwrap
import warnings
from argparse import OPTIONAL, ZERO_OR_MORE, ArgumentParser
from collections import OrderedDict
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    get_args,
    get_origin,
)

# types.UnionType was introduced in Python < 3.10
try:  # pragma: no cover
    from types import UnionType

    UNION_TYPES = [Union, UnionType]
except ImportError:  # pragma: no cover
    UNION_TYPES = [Union]

from argh.completion import COMPLETION_ENABLED
from argh.constants import (
    ATTR_ALIASES,
    ATTR_ARGS,
    ATTR_NAME,
    DEFAULT_ARGUMENT_TEMPLATE,
    DEST_FUNCTION,
    PARSER_FORMATTER,
)
from argh.dto import NotDefined, ParserAddArgumentSpec
from argh.exceptions import AssemblingError
from argh.utils import get_subparsers

__all__ = [
    "set_default_command",
    "add_commands",
    "add_subcommands",
    "NameMappingPolicy",
]


class NameMappingPolicy(Enum):
    """
    Represents possible approaches to treat default values when inferring argument
    specification from function signature.

    * `BY_NAME_IF_KWONLY` is the default and recommended approach introduced
      in v0.30.  It enables fine control over two aspects:

      * positional vs named;
      * required vs optional.

      "Normal" arguments are identified by position, "kwonly" are identified by
      name, regardless of the presence of default values.  A positional with a
      default value becomes optional but still positional (``nargs=OPTIONAL``).
      A kwonly argument without a default value becomes a required named
      argument.

      Example::

          def func(alpha, beta=1, *, gamma, delta=2): ...

      is equivalent to::

          prog alpha [beta] --gamma [--delta DELTA]

      That is, ``alpha`` and ``--gamma`` are mandatory while ``beta`` and
      ``--delta`` are optional (they have default values).

    * `BY_NAME_IF_HAS_DEFAULT` is very close to the the legacy approach
      (pre-v0.30).  If a function argument has a default value, it becomes an
      "option" (called by name, like ``--foo``); otherwise it's treated as a
      positional argument.

      Example::

          def func(alpha, beta=1, *, gamma, delta=2): ...

      is equivalent to::

          prog [--beta BETA] [--delta DELTA] alpha gamma

      That is, ``alpha`` and ``gamma`` are mandatory and positional, while
      ``--beta`` and ``--delta`` are optional (they have default values).  Note
      that it's impossible to have an optional positional or a mandatory named
      argument.

      The difference between this policy and the behaviour of Argh before
      v0.30 is in the treatment of kwonly arguments without default values:
      they used to become ``--foo FOO`` (required) but for the sake of
      simplicity they are treated as positionals.  If you are already using
      kwonly args, please consider the better suited policy `BY_NAME_IF_KWONLY`
      instead.

    It is recommended to migrate any older code to `BY_NAME_IF_KWONLY`.

    .. versionadded:: 0.30
    """

    BY_NAME_IF_HAS_DEFAULT = "specify CLI argument by name if it has a default value"
    BY_NAME_IF_KWONLY = "specify CLI argument by name if it comes from kwonly"


def infer_argspecs_from_function(
    function: Callable,
    name_mapping_policy: Optional[NameMappingPolicy] = None,
    can_use_hints: bool = False,
) -> Iterator[ParserAddArgumentSpec]:
    if name_mapping_policy and name_mapping_policy not in NameMappingPolicy:
        raise NotImplementedError(f"Unknown name mapping policy {name_mapping_policy}")

    func_signature = inspect.signature(function)
    has_kwonly = any(
        p.kind == p.KEYWORD_ONLY for p in func_signature.parameters.values()
    )

    # define the list of conflicting option strings
    # (short forms, i.e. single-character ones)
    named_args = [
        p.name
        for p in func_signature.parameters.values()
        if p.default is not p.empty or p.kind == p.KEYWORD_ONLY
    ]
    named_arg_chars = [a[0] for a in named_args]
    named_arg_char_counts = dict(
        (char, named_arg_chars.count(char)) for char in set(named_arg_chars)
    )
    conflicting_opts = tuple(
        char for char in named_arg_char_counts if 1 < named_arg_char_counts[char]
    )

    def _make_cli_arg_names_options(arg_name) -> Tuple[List[str], List[str]]:
        cliified_arg_name = arg_name.replace("_", "-")
        positionals = [cliified_arg_name]
        can_have_short_opt = arg_name[0] not in conflicting_opts

        if can_have_short_opt:
            options = [f"-{cliified_arg_name[0]}", f"--{cliified_arg_name}"]
        else:
            options = [f"--{cliified_arg_name}"]

        return positionals, options

    default_value: Any
    for parameter in func_signature.parameters.values():
        (cli_arg_names_positional, cli_arg_names_options) = _make_cli_arg_names_options(
            parameter.name
        )
        if parameter.default is not parameter.empty:
            default_value = parameter.default
        else:
            default_value = NotDefined

        extra_spec_kwargs = {}

        if can_use_hints:
            hints = function.__annotations__
            if parameter.name in hints:
                extra_spec_kwargs = (
                    TypingHintArgSpecGuesser.typing_hint_to_arg_spec_params(
                        hints[parameter.name]
                    )
                )

        if parameter.kind in (
            parameter.POSITIONAL_ONLY,
            parameter.POSITIONAL_OR_KEYWORD,
        ):
            if default_value != NotDefined and not name_mapping_policy:
                message = textwrap.dedent(
                    f"""
                    Argument "{parameter.name}" in function "{function.__name__}"
                    is not keyword-only but has a default value.

                    Please note that since Argh v.0.30 the default name mapping
                    policy has changed.

                    More information:
                    https://argh.readthedocs.io/en/latest/changes.html#version-0-30-0-2023-10-21

                    You need to upgrade your functions so that the arguments
                    that have default values become keyword-only:

                        f(x=1) -> f(*, x=1)

                    If you actually want an optional positional argument,
                    please set the name mapping policy explicitly to `BY_NAME_IF_KWONLY`.

                    If you choose to postpone the migration, you have two options:

                    a) set the policy explicitly to `BY_NAME_IF_HAS_DEFAULT`;
                    b) pin Argh version to 0.29 until you are ready to migrate.

                    Thank you for understanding!
                    """
                ).strip()

                # Assume legacy policy and show a warning if the signature is
                # simple (without kwonly args) so that the script continues working
                # but the author is urged to upgrade it.
                # When it cannot be auto-resolved (kwonly args mixed with old-style
                # ones but no policy specified), throw an error.
                #
                # TODO: remove in v.0.33 if it happens, otherwise in v1.0.
                if has_kwonly:
                    raise ArgumentNameMappingError(message)
                warnings.warn(DeprecationWarning(message))
                name_mapping_policy = NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT

            arg_spec = ParserAddArgumentSpec(
                func_arg_name=parameter.name,
                cli_arg_names=cli_arg_names_positional,
                default_value=default_value,
                other_add_parser_kwargs=extra_spec_kwargs,
            )

            if default_value != NotDefined:
                if name_mapping_policy == NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT:
                    arg_spec.cli_arg_names = cli_arg_names_options
                else:
                    arg_spec.nargs = OPTIONAL

            # annotations are interpreted without regard to the broader
            # context, e.g. default values; in some cases argparse requires
            # pretty specific combinations of props, so we need to adjust them
            if can_use_hints:
                # "required" is invalid for positional CLI argument;
                # it may have been set from Optional[...] hint above.
                # Reinterpret it as "optional positional" instead.
                if "required" in arg_spec.other_add_parser_kwargs:
                    value = arg_spec.other_add_parser_kwargs.pop("required")
                    if value is False:
                        arg_spec.nargs = OPTIONAL

                if name_mapping_policy == NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT:
                    # The guesser yields `type=bool` from `foo: bool = False`
                    # but `type` is incompatible with `action="store_true"` which
                    # is added by guess_extra_parser_add_argument_spec_kwargs().
                    if (
                        isinstance(arg_spec.default_value, bool)
                        and arg_spec.other_add_parser_kwargs.get("type") == bool
                    ):
                        del arg_spec.other_add_parser_kwargs["type"]

            yield arg_spec

        elif parameter.kind == parameter.KEYWORD_ONLY:
            arg_spec = ParserAddArgumentSpec(
                func_arg_name=parameter.name,
                cli_arg_names=cli_arg_names_positional,
                default_value=default_value,
                other_add_parser_kwargs=extra_spec_kwargs,
            )

            if name_mapping_policy == NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT:
                if default_value != NotDefined:
                    arg_spec.cli_arg_names = cli_arg_names_options
            else:
                arg_spec.cli_arg_names = cli_arg_names_options
                if default_value == NotDefined:
                    arg_spec.is_required = True

            # annotations are interpreted without regard to the broader
            # context, e.g. default values; in some cases argparse requires
            # pretty specific combinations of props, so we need to adjust them
            if can_use_hints:
                # The guesser yields `type=bool` from `foo: bool = False`
                # but `type` is incompatible with `action="store_true"` which
                # is added by guess_extra_parser_add_argument_spec_kwargs().
                if (
                    isinstance(arg_spec.default_value, bool)
                    and arg_spec.other_add_parser_kwargs.get("type") == bool
                ):
                    del arg_spec.other_add_parser_kwargs["type"]

            yield arg_spec

        elif parameter.kind == parameter.VAR_POSITIONAL:
            yield ParserAddArgumentSpec(
                func_arg_name=parameter.name,
                cli_arg_names=[parameter.name.replace("_", "-")],
                nargs=ZERO_OR_MORE,
                other_add_parser_kwargs=extra_spec_kwargs,
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
    # TODO: use typing to extract
    other_add_parser_kwargs = parser_add_argument_spec.other_add_parser_kwargs
    guessed: Dict[str, Any] = {}
    is_positional = not parser_add_argument_spec.cli_arg_names[0].startswith("-")

    # Parser actions that accept argument 'type'
    TYPE_AWARE_ACTIONS = "store", "append"

    # guess type/action from default value
    default_value = parser_add_argument_spec.default_value
    if default_value not in (None, NotDefined):
        if isinstance(default_value, bool):
            if not is_positional and other_add_parser_kwargs.get("action") is None:
                # infer action from default value
                # (not applicable to positionals: _StoreAction doesn't accept `nargs`)
                guessed["action"] = "store_false" if default_value else "store_true"
        elif other_add_parser_kwargs.get("type") is None:
            if isinstance(default_value, (list, tuple)):
                if "nargs" not in other_add_parser_kwargs:
                    # the argument has a default value, so it doesn't have to
                    # be passed; "zero or more" is a reasonable guess
                    guessed["nargs"] = ZERO_OR_MORE
            else:
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


def set_default_command(
    parser,
    function: Callable,
    name_mapping_policy: Optional[NameMappingPolicy] = None,
) -> None:
    """
    Sets default command (i.e. a function) for given parser.

    If `parser.description` is empty and the function has a docstring,
    it is used as the description.

    :param function:

        The function to use as the command.

    :name_mapping_policy:

        The policy to use when mapping function arguments onto CLI arguments.
        See :class:`.NameMappingPolicy`.  If not defined explicitly,
        `BY_NAME_IF_KWONLY` is used.

        .. versionadded:: 0.30

        .. versionchanged:: 0.30.2
           Raises `ArgumentNameMappingError` if the policy was not explicitly
           defined and a non-kwonly argument has a default value.  The reason
           is that it's very likely to be a case of non-migrated code where
           the argument was intended to be mapped onto a CLI option.  It's
           better to fail explicitly than to silently change the CLI API.

    .. note::

       If there are both explicitly declared arguments (e.g. via
       :func:`~argh.decorators.arg`) and ones inferred from the function
       signature, declared ones will be merged into inferred ones.
       If an argument does not conform to the function signature,
       `ArgumentNameMappingError` is raised.

    .. note::

       If the parser was created with ``add_help=True`` (which is by default),
       option name ``-h`` is silently removed from any argument.

    """
    func_signature = inspect.signature(function)

    # the **kwargs thing
    has_varkw = any(p.kind == p.VAR_KEYWORD for p in func_signature.parameters.values())

    declared_args: List[ParserAddArgumentSpec] = getattr(function, ATTR_ARGS, [])

    # transitional period: hints are used for types etc. only if @arg is not used
    can_use_hints = not declared_args

    inferred_args: List[ParserAddArgumentSpec] = list(
        infer_argspecs_from_function(
            function,
            name_mapping_policy=name_mapping_policy,
            can_use_hints=can_use_hints,
        )
    )

    if declared_args and not inferred_args and not has_varkw:
        raise ArgumentNameMappingError(
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
            )
        except ArgumentNameMappingError as exc:
            raise ArgumentNameMappingError(f"{function.__name__}: {exc}") from exc

    # add the fully formed argument specs to the parser
    for spec in parser_add_argument_specs:
        _extend_parser_add_argument_spec(
            spec=spec, parser_adds_help_arg=parser.add_help
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


def _extend_parser_add_argument_spec(
    spec: ParserAddArgumentSpec, parser_adds_help_arg: bool
) -> None:
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


def _merge_inferred_and_declared_args(
    inferred_args: List[ParserAddArgumentSpec],
    declared_args: List[ParserAddArgumentSpec],
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
    #   it is obtained either from infer_argspecs_from_function()
    #   or from an @arg decorator (as is).
    #
    specs_by_func_arg_name = OrderedDict()

    # arguments inferred from function signature
    for parser_add_argument_spec in inferred_args:
        specs_by_func_arg_name[parser_add_argument_spec.func_arg_name] = (
            parser_add_argument_spec
        )

    # arguments declared via @arg decorator
    for declared_spec in declared_args:
        parser_add_argument_spec = declared_spec
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
                raise ArgumentNameMappingError(
                    f'argument "{func_arg_name}" declared as {kind_inferred} '
                    f"(in function signature) and {kind_declared} (via decorator). "
                    "If you've just migrated from Argh v.0.29, please check "
                    "the new default NameMappingPolicy. Perhaps you need "
                    "to replace `func(x=1)` with `func(*, x=1)`?"
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
                raise ArgumentNameMappingError(
                    f"argument {msg_flags} does not fit "
                    f"function signature: {msg_signature}"
                )

    # pack the modified data back into a list
    return list(specs_by_func_arg_name.values())


def _is_positional(args: List[str], prefix_chars: str = "-") -> bool:
    if not args or not args[0]:
        raise ValueError("Expected at least one argument")
    if args[0][0].startswith(tuple(prefix_chars)):
        return False
    return True


def add_commands(
    parser: ArgumentParser,
    functions: List[Callable],
    name_mapping_policy: Optional[NameMappingPolicy] = None,
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

    :param name_mapping_policy:

        See :class:`argh.assembling.NameMappingPolicy`.

        .. versionadded:: 0.30

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
        set_default_command(
            command_parser, func, name_mapping_policy=name_mapping_policy
        )


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

        add_commands(
            parser,
            [get, put],
            group_name="db",
            group_kwargs={
                "title": "database commands",
                "help": "CRUD for our silly database"
            }
        )

        add_subcommands(
            parser,
            "db",
            [get, put],
            title="database commands",
            help="CRUD for our database"
        )

    """
    add_commands(parser, functions, group_name=group_name, group_kwargs=group_kwargs)


class ArgumentNameMappingError(AssemblingError): ...


class TypingHintArgSpecGuesser:
    BASIC_TYPES = (str, int, float, bool)

    @classmethod
    def typing_hint_to_arg_spec_params(
        cls, type_def: type, is_positional: bool = False
    ) -> Dict[str, Any]:
        origin = get_origin(type_def)
        args = get_args(type_def)

        # `str`
        if type_def in cls.BASIC_TYPES:
            return {
                "type": type_def
                # "type": _parse_basic_type(type_def)
            }

        # `list`
        if type_def in (list, List):
            return {"nargs": ZERO_OR_MORE}

        # `Literal["a", "b"]`
        if origin == Literal:
            return {"choices": args, "type": type(args[0])}

        # `str | int`
        if any(origin is t for t in UNION_TYPES):
            retval = {}
            first_subtype = args[0]
            if first_subtype in cls.BASIC_TYPES:
                retval["type"] = first_subtype

            if first_subtype in (list, List):
                retval["nargs"] = ZERO_OR_MORE

            if first_subtype != List and get_origin(first_subtype) == list:
                retval["nargs"] = ZERO_OR_MORE
                item_type = cls._extract_item_type_from_list_type(first_subtype)
                if item_type:
                    retval["type"] = item_type

            if type(None) in args:
                retval["required"] = False
            return retval

        # `list[str]`
        if origin == list:
            retval = {}
            retval["nargs"] = ZERO_OR_MORE
            if args[0] in cls.BASIC_TYPES:
                retval["type"] = args[0]
            return retval

        return {}

    @classmethod
    def _extract_item_type_from_list_type(cls, type_def) -> Optional[type]:
        args = get_args(type_def)
        if args[0] in cls.BASIC_TYPES:
            return args[0]
        return None
