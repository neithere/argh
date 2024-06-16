"""
Integration Tests
~~~~~~~~~~~~~~~~~
"""

import argparse
import re
import sys
import unittest.mock as mock
from enum import Enum

import pytest

import argh
from argh.assembling import NameMappingPolicy
from argh.exceptions import AssemblingError
from argh.utils import unindent

from .base import CmdResult as R
from .base import DebugArghParser, get_usage_string, run

if sys.version_info < (3, 10):
    HELP_OPTIONS_LABEL = "optional arguments"
else:
    HELP_OPTIONS_LABEL = "options"


def test_set_default_command_integration():
    def cmd(*, foo=1):
        return foo

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "") == R(out="1\n", err="")
    assert run(parser, "--foo 2") == R(out="2\n", err="")
    assert run(parser, "--help", exit=True) == 0


def test_set_default_command_integration_merging():
    @argh.arg("--foo", help="bar")
    def cmd(*, foo=1):
        return foo

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "") == R(out="1\n", err="")
    assert run(parser, "--foo 2") == R(out="2\n", err="")
    assert "bar" in parser.format_help()


#
# Function can be added to parser as is
#


def test_simple_function_no_args():
    def cmd():
        yield 1

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "") == R(out="1\n", err="")


def test_simple_function_positional():
    def cmd(x):
        yield x

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "", exit=True) == "the following arguments are required: x"
    assert run(parser, "foo") == R(out="foo\n", err="")


def test_simple_function_defaults():
    def cmd(*, x="foo"):
        yield x

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "") == R(out="foo\n", err="")
    assert run(parser, "bar", exit=True) == "unrecognized arguments: bar"
    assert run(parser, "--x bar") == R(out="bar\n", err="")


def test_simple_function_varargs():
    def func(*file_paths):
        # `paths` is the single positional argument with nargs="*"
        yield ", ".join(file_paths)

    parser = DebugArghParser()
    parser.set_default_command(func)

    assert run(parser, "") == R(out="\n", err="")
    assert run(parser, "foo") == R(out="foo\n", err="")
    assert run(parser, "foo bar") == R(out="foo, bar\n", err="")


def test_simple_function_kwargs():
    @argh.arg("foo")
    @argh.arg("--bar")
    def cmd(**kwargs):
        # `kwargs` contain all arguments not fitting ArgSpec.args and .varargs.
        # if ArgSpec.keywords in None, all @arg()'s will have to fit ArgSpec.args
        for k in sorted(kwargs):
            yield f"{k}: {kwargs[k]}"

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    message = "the following arguments are required: foo"
    assert run(parser, "", exit=True) == message
    assert run(parser, "hello") == R(out="bar: None\nfoo: hello\n", err="")
    assert run(parser, "--bar 123", exit=True) == message
    assert run(parser, "hello --bar 123") == R(out="bar: 123\nfoo: hello\n", err="")


def test_all_specs_in_one():
    @argh.arg("foo")
    @argh.arg("--bar")
    @argh.arg("fox")
    @argh.arg("--baz")
    def cmd(foo, *args, bar=1, **kwargs):
        yield f"foo: {foo}"
        yield f"bar: {bar}"
        yield f"*args: {args}"
        for k in sorted(kwargs):
            yield f"** {k}: {kwargs[k]}"

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    # 1) bar=1 is treated as --bar so positionals from @arg that go **kwargs
    #    will still have higher priority than bar.
    # 2) *args, a positional with nargs="*", sits between two required
    #    positionals (foo and fox), so it gets nothing.
    assert run(parser, "one two") == R(
        out="foo: one\n" "bar: 1\n" "*args: ()\n" "** baz: None\n" "** fox: two\n",
        err="",
    )

    # two required positionals (foo and fox) get an argument each and one extra
    # is left; therefore the middle one is given to *args.
    assert run(parser, "one two three") == R(
        out="foo: one\n"
        "bar: 1\n"
        "*args: ('two',)\n"
        "** baz: None\n"
        "** fox: three\n",
        err="",
    )

    # two required positionals (foo and fox) get an argument each and two extra
    # are left; both are given to *args (it's greedy).
    assert run(parser, "one two three four") == R(
        out="foo: one\n"
        "bar: 1\n"
        "*args: ('two', 'three')\n"
        "** baz: None\n"
        "** fox: four\n",
        err="",
    )


def test_arg_merged():
    """@arg merges into function signature."""

    @argh.arg("my", help="a moose once bit my sister")
    @argh.arg("-b", "--brain", help="i am made entirely of wood")
    def gumby(my, *, brain=None):
        return my, brain, "hurts"

    parser = DebugArghParser("PROG")
    parser.set_default_command(gumby)
    help_msg = parser.format_help()

    assert "a moose once bit my sister" in help_msg
    assert "i am made entirely of wood" in help_msg


def test_arg_mismatch_positional():
    """An `@arg("positional")` must match function signature."""

    @argh.arg("bogus-argument")
    def confuse_a_cat(vet, *, funny_things=123):
        return vet, funny_things

    parser = DebugArghParser("PROG")
    with pytest.raises(AssemblingError) as excinfo:
        parser.set_default_command(confuse_a_cat)

    msg = (
        "confuse_a_cat: argument bogus-argument does not fit "
        "function signature: vet, -f/--funny-things"
    )
    assert msg in str(excinfo.value)


def test_arg_mismatch_flag():
    """An `@arg("--flag")` must match function signature."""

    @argh.arg("--bogus-argument")
    def confuse_a_cat(vet, *, funny_things=123):
        return vet, funny_things

    parser = DebugArghParser("PROG")
    with pytest.raises(AssemblingError) as excinfo:
        parser.set_default_command(confuse_a_cat)

    msg = (
        "confuse_a_cat: argument --bogus-argument does not fit "
        "function signature: vet, -f/--funny-things"
    )
    assert msg in str(excinfo.value)


def test_arg_mismatch_positional_vs_flag():
    """An `@arg("arg")` must match a positional arg in function signature."""

    @argh.arg("foo")
    def func(*, foo=123):
        return foo

    parser = DebugArghParser("PROG")
    with pytest.raises(AssemblingError) as excinfo:
        parser.set_default_command(func)

    msg = (
        'func: argument "foo" declared as optional (in function signature)'
        " and positional (via decorator)"
    )
    assert msg in str(excinfo.value)


def test_arg_mismatch_flag_vs_positional():
    """An `@arg("--flag")` must match a keyword in function signature."""

    @argh.arg("--foo")
    def func(foo):
        return foo

    parser = DebugArghParser("PROG")
    with pytest.raises(AssemblingError) as excinfo:
        parser.set_default_command(func)

    msg = (
        'func: argument "foo" declared as positional (in function signature)'
        " and optional (via decorator)"
    )
    assert msg in str(excinfo.value)


class TestErrorWrapping:
    def _get_parrot(self):
        def parrot(*, dead=False):
            if dead:
                raise ValueError("this parrot is no more")
            else:
                return "beautiful plumage"

        return parrot

    def test_error_raised(self):
        parrot = self._get_parrot()

        parser = DebugArghParser()
        parser.set_default_command(parrot)

        assert run(parser, "") == R("beautiful plumage\n", "")
        with pytest.raises(ValueError) as excinfo:
            run(parser, "--dead")
        assert re.match("this parrot is no more", str(excinfo.value))

    def test_error_wrapped(self):
        parrot = self._get_parrot()
        wrapped_parrot = argh.wrap_errors([ValueError])(parrot)

        parser = DebugArghParser()
        parser.set_default_command(wrapped_parrot)

        assert run(parser, "") == R("beautiful plumage\n", "")
        assert run(parser, "--dead") == R(
            "", "ValueError: this parrot is no more\n", exit_code=1
        )

    def test_processor(self):
        parrot = self._get_parrot()
        wrapped_parrot = argh.wrap_errors([ValueError])(parrot)

        def failure(err):
            return "ERR: " + str(err) + "!"

        processed_parrot = argh.wrap_errors(processor=failure)(wrapped_parrot)

        parser = argh.ArghParser()
        parser.set_default_command(processed_parrot)

        assert run(parser, "--dead") == R(
            "", "ERR: this parrot is no more!\n", exit_code=1
        )

    def test_stderr_vs_stdout(self):
        @argh.wrap_errors([KeyError])
        def func(key):
            db = {"a": 1}
            return db[key]

        parser = argh.ArghParser()
        parser.set_default_command(func)

        assert run(parser, "a") == R(out="1\n", err="")
        assert run(parser, "b") == R(out="", err="KeyError: 'b'\n", exit_code=1)


def test_argv():
    def echo(text):
        return f"you said {text}"

    parser = DebugArghParser()
    parser.add_commands([echo])

    _argv = sys.argv

    sys.argv = sys.argv[:1] + ["echo", "hi there"]
    assert run(parser, None) == R("you said hi there\n", "")

    sys.argv = _argv


def test_commands_not_defined():
    parser = DebugArghParser()

    assert run(parser, "", {"raw_output": True}).out == parser.format_usage()
    assert run(parser, "").out == parser.format_usage()

    assert "unrecognized arguments" in run(parser, "foo", exit=True)
    assert "unrecognized arguments" in run(parser, "--foo", exit=True)


def test_command_not_chosen():
    def cmd(args):
        return 1

    parser = DebugArghParser()
    parser.add_commands([cmd])

    # returns a help message and doesn't exit
    assert "usage:" in run(parser, "").out


def test_invalid_choice():
    def cmd(args):
        return 1

    # root level command

    parser = DebugArghParser()
    parser.add_commands([cmd])

    assert "invalid choice" in run(parser, "bar", exit=True)

    # exits with an informative error
    assert run(parser, "--bar", exit=True) == "unrecognized arguments: --bar"

    # nested command

    parser = DebugArghParser()
    parser.add_commands([cmd], group_name="nest")

    assert "invalid choice" in run(parser, "nest bar", exit=True)

    # exits with an informative error
    assert run(parser, "nest --bar", exit=True) == "unrecognized arguments: --bar"


def test_unrecognized_arguments():
    def cmd():
        return 1

    # single-command parser

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "--bar", exit=True) == "unrecognized arguments: --bar"
    assert run(parser, "bar", exit=True) == "unrecognized arguments: bar"

    # multi-command parser

    parser = DebugArghParser()
    parser.add_commands([cmd])

    assert run(parser, "cmd --bar", exit=True) == "unrecognized arguments: --bar"
    assert run(parser, "cmd bar", exit=True) == "unrecognized arguments: bar"


def test_echo():
    "A simple command is resolved to a function."

    def echo(text):
        return f"you said {text}"

    parser = DebugArghParser()
    parser.add_commands([echo])

    assert run(parser, "echo foo") == R(out="you said foo\n", err="")


def test_bool_action():
    "Action `store_true`/`store_false` is inferred from default value."

    def parrot(*, dead=False):
        return "this parrot is no more" if dead else "beautiful plumage"

    parser = DebugArghParser()
    parser.add_commands([parrot])

    assert run(parser, "parrot").out == "beautiful plumage\n"
    assert run(parser, "parrot --dead").out == "this parrot is no more\n"


def test_bare_group_name():
    "A command can be resolved to a function, not a group_name."

    def hello():
        return "hello world"

    parser = DebugArghParser()
    parser.add_commands([hello], group_name="greet")

    # without arguments

    # returns a help message and doesn't exit
    assert "usage:" in run(parser, "greet").out

    # with an argument

    # exits with an informative error
    message = "unrecognized arguments: --name=world"
    assert run(parser, "greet --name=world", exit=True) == message


def test_function_under_group_name():
    "A subcommand is resolved to a function."

    def hello(*, name="world"):
        return f"Hello {name}!"

    def howdy(buddy):
        return f"Howdy {buddy}?"

    parser = DebugArghParser()
    parser.add_commands([hello, howdy], group_name="greet")

    assert run(parser, "greet hello").out == "Hello world!\n"
    assert run(parser, "greet hello --name=John").out == "Hello John!\n"
    assert run(parser, "greet hello John", exit=True) == "unrecognized arguments: John"

    # exits with an informative error
    message = "the following arguments are required: buddy"

    assert message in run(parser, "greet howdy --name=John", exit=True)
    assert run(parser, "greet howdy John").out == "Howdy John?\n"


def test_explicit_cmd_name():
    @argh.named("new-name")
    def orig_name():
        return "ok"

    parser = DebugArghParser()
    parser.add_commands([orig_name])
    assert "invalid choice" in run(parser, "orig-name", exit=True)
    assert run(parser, "new-name").out == "ok\n"


def test_aliases():
    @argh.aliases("alias2", "alias3")
    def alias1():
        return "ok"

    parser = DebugArghParser()
    parser.add_commands([alias1])

    assert run(parser, "alias1").out == "ok\n"
    assert run(parser, "alias2").out == "ok\n"
    assert run(parser, "alias3").out == "ok\n"


def test_help():
    parser = DebugArghParser()

    # assert the commands don't fail
    assert run(parser, "--help", exit=True) == 0
    assert run(parser, "greet --help", exit=True) == 0
    assert run(parser, "greet hello --help", exit=True) == 0


def test_arg_order():
    """Positional arguments are resolved in the order in which the @arg
    decorators are defined.
    """

    def cmd(foo, bar):
        return foo, bar

    parser = DebugArghParser()
    parser.set_default_command(cmd)
    assert run(parser, "foo bar").out == "foo\nbar\n"


def test_raw_output():
    "If the raw_output flag is set, no extra whitespace is added"

    def cmd(foo, bar):
        return foo, bar

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "foo bar").out == "foo\nbar\n"
    assert run(parser, "foo bar", {"raw_output": True}).out == "foobar"


def test_output_file():
    def cmd():
        return "Hello world!"

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "").out == "Hello world!\n"
    assert run(parser, "", {"output_file": None}).out == "Hello world!\n"


def test_command_error():
    def whiner_plain(*, code=1):
        raise argh.CommandError("I feel depressed.", code=code)

    def whiner_iterable():
        yield "Hello..."
        raise argh.CommandError("I feel depressed.")

    parser = DebugArghParser()
    parser.add_commands([whiner_plain, whiner_iterable])

    assert run(parser, "whiner-plain") == R(
        out="", err="CommandError: I feel depressed.\n", exit_code=1
    )
    assert run(parser, "whiner-plain --code=127") == R(
        out="", err="CommandError: I feel depressed.\n", exit_code=127
    )
    assert run(parser, "whiner-iterable") == R(
        out="Hello...\n", err="CommandError: I feel depressed.\n", exit_code=1
    )


@pytest.mark.parametrize(
    "argparse_namespace_class", [argparse.Namespace, argh.dispatching.ArghNamespace]
)
def test_get_function_from_namespace_obj(argparse_namespace_class):
    argparse_namespace = argparse_namespace_class()

    def func():
        pass

    retval = argh.dispatching._get_function_from_namespace_obj(argparse_namespace)
    assert retval is None

    setattr(argparse_namespace, argh.constants.DEST_FUNCTION, "")

    retval = argh.dispatching._get_function_from_namespace_obj(argparse_namespace)
    assert retval is None

    setattr(argparse_namespace, argh.constants.DEST_FUNCTION, func)

    retval = argh.dispatching._get_function_from_namespace_obj(argparse_namespace)
    assert retval == func


def test_normalized_keys():
    """Underscores in function args are converted to dashes and back."""

    def cmd(a_b):
        return a_b

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    assert run(parser, "hello").out == "hello\n"


@mock.patch("argh.assembling.COMPLETION_ENABLED", True)
def test_custom_argument_completer():
    "Issue #33: Enable custom per-argument shell completion"

    @argh.arg("foo", completer="STUB")
    def func(foo):
        pass

    parser = argh.ArghParser()
    parser.set_default_command(func)

    assert parser._actions[-1].completer == "STUB"


def test_class_members():
    "Issue #34: class members as commands"

    class Controller:
        var = 123

        def instance_meth(self, value):
            return value, self.var

        @classmethod
        def class_meth(cls, value):
            return value, cls.var

        @staticmethod
        def static_meth(value):
            return value, "w00t?"

        @staticmethod
        def static_meth2(value):
            return value, "huh!"

    controller = Controller()

    parser = DebugArghParser()
    parser.add_commands(
        [
            controller.instance_meth,
            controller.class_meth,
            controller.static_meth,
            Controller.static_meth2,
        ]
    )

    assert run(parser, "instance-meth foo").out == "foo\n123\n"
    assert run(parser, "class-meth foo").out == "foo\n123\n"
    assert run(parser, "static-meth foo").out == "foo\nw00t?\n"
    assert run(parser, "static-meth2 foo").out == "foo\nhuh!\n"


def test_kwonlyargs__policy_legacy():
    "Correct dispatch in presence of keyword-only arguments"

    def cmd(*args, foo="1", bar, baz="3", **kwargs):
        return f"foo='{foo}' bar='{bar}' baz='{baz}' args={args} kwargs={kwargs}"

    parser = DebugArghParser(prog="pytest")
    parser.set_default_command(
        cmd, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT
    )

    expected_usage = "usage: pytest [-h] [-f FOO] [--baz BAZ] [args ...] bar\n"
    if sys.version_info < (3, 9):
        # https://github.com/python/cpython/issues/82619
        expected_usage = (
            "usage: pytest [-h] [-f FOO] [--baz BAZ] [args [args ...]] bar\n"
        )
    assert parser.format_usage() == expected_usage

    assert (
        run(parser, "--baz=baz! one  two").out
        == "foo='1' bar='two' baz='baz!' args=('one',) kwargs={}\n"
    )
    assert (
        run(parser, "test --foo=do").out
        == "foo='do' bar='test' baz='3' args=() kwargs={}\n"
    )


def test_kwonlyargs__policy_modern():
    "Correct dispatch in presence of keyword-only arguments"

    def cmd(*args, foo="1", bar, baz="3", **kwargs):
        return f"foo='{foo}' bar='{bar}' baz='{baz}' args={args} kwargs={kwargs}"

    parser = DebugArghParser(prog="pytest")
    parser.set_default_command(
        cmd, name_mapping_policy=NameMappingPolicy.BY_NAME_IF_KWONLY
    )

    expected_usage = "usage: pytest [-h] [-f FOO] --bar BAR [--baz BAZ] [args ...]\n"
    if sys.version_info < (3, 9):
        # https://github.com/python/cpython/issues/82619
        expected_usage = (
            "usage: pytest [-h] [-f FOO] --bar BAR [--baz BAZ] [args [args ...]]\n"
        )
    assert parser.format_usage() == expected_usage

    assert (
        run(parser, "--baz=baz! one  two --bar=bar!").out
        == "foo='1' bar='bar!' baz='baz!' args=('one', 'two') kwargs={}\n"
    )
    message = "the following arguments are required: --bar"
    assert run(parser, "test --foo=do", exit=True) == message


def test_default_arg_values_in_help():
    "Argument defaults should appear in the help message implicitly"

    @argh.arg("name", default="Basil")
    @argh.arg("--task", default="hang the Moose")
    @argh.arg("--note", help="why is it a remarkable animal?")
    def remind(
        name,
        *,
        task=None,
        reason="there are creatures living in it",
        note="it can speak English",
    ):
        return "Oh what is it now, can't you leave me in peace..."

    parser = DebugArghParser()
    parser.set_default_command(remind)

    help_normalised = re.sub(r"\s+", " ", parser.format_help())

    assert "name 'Basil'" in help_normalised

    # argh#228 — argparse in Python before 3.13 duplicated the placeholder in help
    if sys.version_info < (3, 13):
        assert "-t TASK, --task TASK 'hang the Moose'" in help_normalised
        assert (
            "-r REASON, --reason REASON 'there are creatures living in it'"
            in help_normalised
        )

        # explicit help message is not obscured by the implicit one
        # but is still present
        assert (
            "-n NOTE, --note NOTE why is it a remarkable animal? "
            "(default: 'it can speak English')"
        ) in help_normalised
    else:
        assert "-t, --task TASK 'hang the Moose'" in help_normalised
        assert (
            "-r, --reason REASON 'there are creatures living in it'" in help_normalised
        )

        # explicit help message is not obscured by the implicit one
        # but is still present
        assert (
            "-n, --note NOTE why is it a remarkable animal? "
            "(default: 'it can speak English')"
        ) in help_normalised


def test_default_arg_values_in_help__regression():
    "Empty string as default value → empty help string → broken argparse"

    def foo(*, bar=""):
        return bar

    parser = DebugArghParser()
    parser.set_default_command(foo)

    # doesn't break
    parser.format_help()

    # argh#228 — argparse in Python before 3.13 duplicated the placeholder in help
    if sys.version_info < (3, 13):
        expected_line = "-b BAR, --bar BAR  ''"
        # note the empty str repr         ^^^
    else:
        expected_line = "-b, --bar BAR  ''"
        # note the empty str repr     ^^^

    # now check details
    assert expected_line in parser.format_help()


def test_help_formatting_is_preserved():
    "Formatting of docstrings should not be messed up in help messages"

    def func():
        """
        Sample function.

        Parameters:
            foo: float
                An example argument.
            bar: bool
                Another argument.
        """
        return "hello"

    parser = DebugArghParser()
    parser.set_default_command(func)

    assert unindent(func.__doc__) in parser.format_help()


def test_prog(capsys: pytest.CaptureFixture[str]):
    "Program name propagates from sys.argv[0]"

    def cmd(*, foo=1):
        return foo

    parser = DebugArghParser()
    parser.add_commands([cmd])

    usage = get_usage_string()

    assert run(parser, "-h", exit=True) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith(usage)


def test_unknown_args():
    def cmd(*, foo=1):
        return foo

    parser = DebugArghParser()
    parser.set_default_command(cmd)

    get_usage_string("[-f FOO]")

    assert run(parser, "--foo 1") == R(out="1\n", err="")
    assert run(parser, "--bar 1", exit=True) == "unrecognized arguments: --bar 1"
    assert run(parser, "--bar 1", exit=False, kwargs={"skip_unknown_args": True}) == R(
        out="1\n", err=""
    )


def test_add_commands_unknown_name_mapping_policy():
    def func(foo): ...

    parser = argh.ArghParser(prog="myapp")

    class UnsuitablePolicyContainer(Enum):
        FOO = "Ni!!!"

    with pytest.raises(
        NotImplementedError,
        match="Unknown name mapping policy UnsuitablePolicyContainer.FOO",
    ):
        parser.add_commands([func], name_mapping_policy=UnsuitablePolicyContainer.FOO)


def test_add_commands_no_overrides1(capsys: pytest.CaptureFixture[str]):
    def first_func(*, foo=123):
        """Owl stretching time"""

    def second_func():
        pass

    parser = argh.ArghParser(prog="myapp")
    parser.add_commands(
        [first_func, second_func],
    )

    run(parser, "--help", exit=True)
    captured = capsys.readouterr()
    assert (
        captured.out
        == unindent(
            f"""
        usage: myapp [-h] {{first-func,second-func}} ...

        positional arguments:
          {{first-func,second-func}}
            first-func          Owl stretching time
            second-func

        {HELP_OPTIONS_LABEL}:
          -h, --help            show this help message and exit
        """
        )[1:]
    )


def test_add_commands_no_overrides2(capsys: pytest.CaptureFixture[str]):
    def first_func(*, foo=123):
        """Owl stretching time"""

    def second_func():
        pass

    parser = argh.ArghParser(prog="myapp")
    parser.add_commands([first_func, second_func])

    run(parser, "first-func --help", exit=True)
    captured = capsys.readouterr()

    # argh#228 — argparse in Python before 3.13 duplicated the placeholder in help
    if sys.version_info < (3, 13):
        arg_help_lines = (
            "  -h, --help         show this help message and exit\n"
            "  -f FOO, --foo FOO  123"
        )
    else:
        arg_help_lines = (
            "  -h, --help     show this help message and exit\n" "  -f, --foo FOO  123"
        )

    assert (
        captured.out
        == unindent(
            f"""
        usage: myapp first-func [-h] [-f FOO]

        Owl stretching time

        {HELP_OPTIONS_LABEL}:
        {arg_help_lines}
        """
        )[1:]
    )


def test_add_commands_group_overrides1(capsys: pytest.CaptureFixture[str]):
    """
    When `group_kwargs` is passed to `add_commands()`, its members override
    whatever was specified on function level.
    """

    def first_func(*, foo=123):
        """Owl stretching time"""
        return foo

    def second_func():
        pass

    parser = argh.ArghParser(prog="myapp")
    parser.add_commands(
        [first_func, second_func],
        group_name="my-group",
        group_kwargs={
            "help": "group help override",
            "description": "group description override",
        },
    )

    run(parser, "--help", exit=True)
    captured = capsys.readouterr()
    assert (
        captured.out
        == unindent(
            f"""
        usage: myapp [-h] {{my-group}} ...

        positional arguments:
          {{my-group}}
            my-group

        {HELP_OPTIONS_LABEL}:
          -h, --help  show this help message and exit
        """
        )[1:]
    )


def test_add_commands_group_overrides2(capsys: pytest.CaptureFixture[str]):
    """
    When `group_kwargs` is passed to `add_commands()`, its members override
    whatever was specified on function level.
    """

    def first_func(*, foo=123):
        """Owl stretching time"""
        return foo

    def second_func():
        pass

    parser = argh.ArghParser(prog="myapp")
    parser.add_commands(
        [first_func, second_func],
        group_name="my-group",
        group_kwargs={
            "help": "group help override",
            "description": "group description override",
        },
    )

    run(parser, "my-group --help", exit=True)
    captured = capsys.readouterr()
    assert (
        captured.out
        == unindent(
            f"""
        usage: myapp my-group [-h] {{first-func,second-func}} ...

        {HELP_OPTIONS_LABEL}:
          -h, --help            show this help message and exit

        subcommands:
          group description override

          {{first-func,second-func}}
                                group help override
            first-func          Owl stretching time
            second-func
        """
        )[1:]
    )


def test_add_commands_group_overrides3(capsys: pytest.CaptureFixture[str]):
    """
    When `group_kwargs` is passed to `add_commands()`, its members override
    whatever was specified on function level.
    """

    def first_func(*, foo=123):
        """Owl stretching time"""
        return foo

    def second_func():
        pass

    parser = argh.ArghParser(prog="myapp")
    parser.add_commands(
        [first_func, second_func],
        group_name="my-group",
        group_kwargs={
            "help": "group help override",
            "description": "group description override",
        },
    )

    run(parser, "my-group first-func --help", exit=True)
    captured = capsys.readouterr()

    # argh#228 — argparse in Python before 3.13 duplicated the placeholder in help
    if sys.version_info < (3, 13):
        arg_help_lines = (
            "  -h, --help         show this help message and exit\n"
            "  -f FOO, --foo FOO  123"
        )
    else:
        arg_help_lines = (
            "  -h, --help     show this help message and exit\n" "  -f, --foo FOO  123"
        )

    assert (
        captured.out
        == unindent(
            f"""
        usage: myapp my-group first-func [-h] [-f FOO]

        Owl stretching time

        {HELP_OPTIONS_LABEL}:
        {arg_help_lines}
        """
        )[1:]
    )


def test_add_commands_func_overrides1(capsys: pytest.CaptureFixture[str]):
    """
    When `func_kwargs` is passed to `add_commands()`, its members override
    whatever was specified on function level.
    """

    def first_func(*, foo=123):
        """Owl stretching time"""
        pass

    def second_func():
        pass

    parser = argh.ArghParser(prog="myapp")
    parser.add_commands(
        [first_func, second_func],
        func_kwargs={
            "help": "func help override",
            "description": "func description override",
        },
    )

    run(parser, "--help", exit=True)
    captured = capsys.readouterr()
    assert (
        captured.out
        == unindent(
            f"""
        usage: myapp [-h] {{first-func,second-func}} ...

        positional arguments:
          {{first-func,second-func}}
            first-func          func help override
            second-func         func help override

        {HELP_OPTIONS_LABEL}:
          -h, --help            show this help message and exit
        """
        )[1:]
    )


def test_add_commands_func_overrides2(capsys: pytest.CaptureFixture[str]):
    """
    When `func_kwargs` is passed to `add_commands()`, its members override
    whatever was specified on function level.
    """

    def first_func(*, foo=123):
        """Owl stretching time"""
        pass

    def second_func():
        pass

    parser = argh.ArghParser(prog="myapp")
    parser.add_commands(
        [first_func, second_func],
        func_kwargs={
            "help": "func help override",
            "description": "func description override",
        },
    )

    run(parser, "first-func --help", exit=True)
    captured = capsys.readouterr()

    # argh#228 — argparse in Python before 3.13 duplicated the placeholder in help
    if sys.version_info < (3, 13):
        arg_help_lines = (
            "  -h, --help         show this help message and exit\n"
            "  -f FOO, --foo FOO  123"
        )
    else:
        arg_help_lines = (
            "  -h, --help     show this help message and exit\n" "  -f, --foo FOO  123"
        )

    assert (
        captured.out
        == unindent(
            f"""
        usage: myapp first-func [-h] [-f FOO]

        func description override

        {HELP_OPTIONS_LABEL}:
        {arg_help_lines}
        """
        )[1:]
    )


def test_action_count__only_arg_decorator():
    @argh.arg("-v", "--verbose", action="count", default=0)
    def func(**kwargs):
        verbosity = kwargs.get("verbose")
        return f"verbosity: {verbosity}"

    parser = DebugArghParser()
    parser.set_default_command(func)

    assert run(parser, "").out == "verbosity: 0\n"
    assert run(parser, "-v").out == "verbosity: 1\n"
    assert run(parser, "-vvvv").out == "verbosity: 4\n"


def test_action_count__mixed():
    @argh.arg("-v", "--verbose", action="count")
    def func(*, verbose=0):
        return f"verbosity: {verbose}"

    parser = DebugArghParser()
    parser.set_default_command(func)

    assert run(parser, "").out == "verbosity: 0\n"
    assert run(parser, "-v").out == "verbosity: 1\n"
    assert run(parser, "-vvvv").out == "verbosity: 4\n"
