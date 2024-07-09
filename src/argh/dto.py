"""
Data transfer objects for internal usage.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union


class NotDefined:
    """
    Specifies that an argument should not be passed to
    ArgumentParser.add_argument(), even as None
    """


@dataclass
class ParserAddArgumentSpec:
    """
    DTO, maps CLI arg(s) onto a function arg.
    Ends up in ArgumentParser.add_argument().
    """

    func_arg_name: Optional[str]  # TODO: make it required (needs rearranging the logic)
    cli_arg_names: List[str]
    is_required: Union[bool, Type[NotDefined]] = NotDefined
    default_value: Any = NotDefined
    nargs: Optional[str] = None
    other_add_parser_kwargs: Dict[str, Any] = field(default_factory=dict)

    # https://kislyuk.github.io/argcomplete/#specifying-completers
    completer: Optional[Callable] = None

    def update(self, other: "ParserAddArgumentSpec") -> None:
        for name in other.cli_arg_names:
            if name not in self.cli_arg_names:
                self.cli_arg_names.append(name)

        if other.is_required != NotDefined:
            self.is_required = other.is_required

        if other.default_value != NotDefined:
            self.default_value = other.default_value

        if other.nargs:
            self.nargs = other.nargs

        if other.completer:
            self.completer = other.completer

        self.other_add_parser_kwargs.update(other.other_add_parser_kwargs)

    def get_all_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {}

        if self.is_required != NotDefined:
            kwargs["required"] = self.is_required

        if self.default_value != NotDefined:
            kwargs["default"] = self.default_value

        if self.nargs:
            kwargs["nargs"] = self.nargs

        return dict(kwargs, **self.other_add_parser_kwargs)

    @classmethod
    def make_from_kwargs(
        cls, func_arg_name, cli_arg_names, parser_add_argument_kwargs: Dict[str, Any]
    ) -> "ParserAddArgumentSpec":
        """
        Constructs and returns a `ParserAddArgumentSpec` instance
        according to keyword arguments according to the
        `ArgumentParser.add_argument()` signature.
        """
        kwargs_copy = parser_add_argument_kwargs.copy()
        instance = cls(
            func_arg_name=func_arg_name,
            cli_arg_names=cli_arg_names,
        )
        if "required" in kwargs_copy:
            instance.is_required = kwargs_copy.pop("required")
        if "nargs" in kwargs_copy:
            instance.nargs = kwargs_copy.pop("nargs")
        if "default" in kwargs_copy:
            instance.default_value = kwargs_copy.pop("default")
        if kwargs_copy:
            instance.other_add_parser_kwargs = kwargs_copy
        return instance
