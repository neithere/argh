# coding: utf-8
"""
Integration Tests
~~~~~~~~~~~~~~~~~
"""
import sys
import re
import argparse

import iocapture
try:
    import unittest.mock as mock
except ImportError:
    # FIXME: remove in v.0.28
    import mock
import pytest

import argh
from argh.exceptions import AssemblingError

from .base import DebugArghParser, get_usage_string, run, CmdResult as R


def test_set_default_command_integration():
    def cmd(foo=1):
        return foo

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == R(out='1\n', err='')
    assert run(p, '--foo 2') == R(out='2\n', err='')
    assert run(p, '--help', exit=True) == None


def test_set_default_command_integration_merging():
    @argh.arg('--foo', help='bar')
    def cmd(foo=1):
        return foo

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == R(out='1\n', err='')
    assert run(p, '--foo 2') == R(out='2\n', err='')
    assert 'bar' in p.format_help()


#
# Function can be added to parser as is
#


def test_simple_function_no_args():
    def cmd():
        yield 1

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == R(out='1\n', err='')


def test_simple_function_positional():
    def cmd(x):
        yield x

    p = DebugArghParser()
    p.set_default_command(cmd)

    if sys.version_info < (3,3):
        msg = 'too few arguments'
    else:
        msg = 'the following arguments are required: x'
    assert run(p, '', exit=True) == msg
    assert run(p, 'foo') == R(out='foo\n', err='')


def test_simple_function_defaults():
    def cmd(x='foo'):
        yield x

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '') == R(out='foo\n', err='')
    assert run(p, 'bar', exit=True) == 'unrecognized arguments: bar'
    assert run(p, '--x bar') == R(out='bar\n', err='')


def test_simple_function_varargs():

    def func(*file_paths):
        # `paths` is the single positional argument with nargs='*'
        yield ', '.join(file_paths)

    p = DebugArghParser()
    p.set_default_command(func)

    assert run(p, '') == R(out='\n', err='')
    assert run(p, 'foo') == R(out='foo\n', err='')
    assert run(p, 'foo bar') == R(out='foo, bar\n', err='')


def test_simple_function_kwargs():

    @argh.arg('foo')
    @argh.arg('--bar')
    def cmd(**kwargs):
        # `kwargs` contain all arguments not fitting ArgSpec.args and .varargs.
        # if ArgSpec.keywords in None, all @arg()'s will have to fit ArgSpec.args
        for k in sorted(kwargs):
            yield '{0}: {1}'.format(k, kwargs[k])

    p = DebugArghParser()
    p.set_default_command(cmd)

    if sys.version_info < (3,3):
        msg = 'too few arguments'
    else:
        msg = 'the following arguments are required: foo'
    assert run(p, '', exit=True) == msg
    assert run(p, 'hello') == R(out='bar: None\nfoo: hello\n', err='')
    assert run(p, '--bar 123', exit=True) == msg
    assert run(p, 'hello --bar 123') == R(out='bar: 123\nfoo: hello\n', err='')


@pytest.mark.xfail
def test_simple_function_multiple():
    raise NotImplementedError


@pytest.mark.xfail
def test_simple_function_nested():
    raise NotImplementedError


@pytest.mark.xfail
def test_class_method_as_command():
    raise NotImplementedError


def test_all_specs_in_one():

    @argh.arg('foo')
    @argh.arg('--bar')
    @argh.arg('fox')
    @argh.arg('--baz')
    def cmd(foo, bar=1, *args, **kwargs):
        yield 'foo: {0}'.format(foo)
        yield 'bar: {0}'.format(bar)
        yield '*args: {0}'.format(args)
        for k in sorted(kwargs):
            yield '** {0}: {1}'.format(k, kwargs[k])

    p = DebugArghParser()
    p.set_default_command(cmd)

    # 1) bar=1 is treated as --bar so positionals from @arg that go **kwargs
    #    will still have higher priority than bar.
    # 2) *args, a positional with nargs='*', sits between two required
    #    positionals (foo and fox), so it gets nothing.
    assert run(p, 'one two') == R(out=
        'foo: one\n'
        'bar: 1\n'
        '*args: ()\n'
        '** baz: None\n'
        '** fox: two\n', err='')

    # two required positionals (foo and fox) get an argument each and one extra
    # is left; therefore the middle one is given to *args.
    assert run(p, 'one two three') == R(out=
        'foo: one\n'
        'bar: 1\n'
        "*args: ('two',)\n"
        '** baz: None\n'
        '** fox: three\n', err='')

    # two required positionals (foo and fox) get an argument each and two extra
    # are left; both are given to *args (it's greedy).
    assert run(p, 'one two three four') == R(out=
        'foo: one\n'
        'bar: 1\n'
        "*args: ('two', 'three')\n"
        '** baz: None\n'
        '** fox: four\n', err='')


def test_arg_merged():
    """ @arg merges into function signature.
    """
    @argh.arg('my', help='a moose once bit my sister')
    @argh.arg('-b', '--brain', help='i am made entirely of wood')
    def gumby(my, brain=None):
        return my, brain, 'hurts'

    p = DebugArghParser('PROG')
    p.set_default_command(gumby)
    help_msg = p.format_help()

    assert 'a moose once bit my sister' in help_msg
    assert 'i am made entirely of wood' in help_msg


def test_arg_mismatch_positional():
    """ An `@arg('positional')` must match function signature.
    """
    @argh.arg('bogus-argument')
    def confuse_a_cat(vet, funny_things=123):
        return vet, funny_things

    p = DebugArghParser('PROG')
    with pytest.raises(AssemblingError) as excinfo:
        p.set_default_command(confuse_a_cat)

    msg = ("confuse_a_cat: argument bogus-argument does not fit "
           "function signature: vet, -f/--funny-things")
    assert msg in str(excinfo.value)


def test_arg_mismatch_flag():
    """ An `@arg('--flag')` must match function signature.
    """
    @argh.arg('--bogus-argument')
    def confuse_a_cat(vet, funny_things=123):
        return vet, funny_things

    p = DebugArghParser('PROG')
    with pytest.raises(AssemblingError) as excinfo:
        p.set_default_command(confuse_a_cat)

    msg = ("confuse_a_cat: argument --bogus-argument does not fit "
           "function signature: vet, -f/--funny-things")
    assert msg in str(excinfo.value)


def test_arg_mismatch_positional_vs_flag():
    """ An `@arg('arg')` must match a positional arg in function signature.
    """
    @argh.arg('foo')
    def func(foo=123):
        return foo

    p = DebugArghParser('PROG')
    with pytest.raises(AssemblingError) as excinfo:
        p.set_default_command(func)

    msg = ('func: argument "foo" declared as optional (in function signature)'
           ' and positional (via decorator)')
    assert msg in str(excinfo.value)


def test_arg_mismatch_flag_vs_positional():
    """ An `@arg('--flag')` must match a keyword in function signature.
    """
    @argh.arg('--foo')
    def func(foo):
        return foo

    p = DebugArghParser('PROG')
    with pytest.raises(AssemblingError) as excinfo:
        p.set_default_command(func)

    msg = ('func: argument "foo" declared as positional (in function signature)'
           ' and optional (via decorator)')
    assert msg in str(excinfo.value)


class TestErrorWrapping:

    def _get_parrot(self):
        def parrot(dead=False):
            if dead:
                raise ValueError('this parrot is no more')
            else:
                return 'beautiful plumage'

        return parrot

    def test_error_raised(self):
        parrot = self._get_parrot()

        p = DebugArghParser()
        p.set_default_command(parrot)

        assert run(p, '') == R('beautiful plumage\n', '')
        with pytest.raises(ValueError) as excinfo:
            run(p, '--dead')
        assert re.match('this parrot is no more', str(excinfo.value))

    def test_error_wrapped(self):
        parrot = self._get_parrot()
        wrapped_parrot = argh.wrap_errors([ValueError])(parrot)

        p = DebugArghParser()
        p.set_default_command(wrapped_parrot)

        assert run(p, '') == R('beautiful plumage\n', '')
        assert run(p, '--dead') == R('', 'ValueError: this parrot is no more\n')

    def test_processor(self):
        parrot = self._get_parrot()
        wrapped_parrot = argh.wrap_errors([ValueError])(parrot)

        def failure(err):
            return 'ERR: ' + str(err) + '!'
        processed_parrot = argh.wrap_errors(processor=failure)(wrapped_parrot)

        p = argh.ArghParser()
        p.set_default_command(processed_parrot)

        assert run(p, '--dead') == R('', 'ERR: this parrot is no more!\n')

    def test_stderr_vs_stdout(self):

        @argh.wrap_errors([KeyError])
        def func(key):
            db = {'a': 1}
            return db[key]

        p = argh.ArghParser()
        p.set_default_command(func)

        assert run(p, 'a') == R(out='1\n', err='')
        assert run(p, 'b') == R(out='', err="KeyError: 'b'\n")


def test_argv():

    def echo(text):
        return 'you said {0}'.format(text)

    p = DebugArghParser()
    p.add_commands([echo])

    _argv = sys.argv

    sys.argv = sys.argv[:1] + ['echo', 'hi there']
    assert run(p, None) == R('you said hi there\n', '')

    sys.argv = _argv


def test_commands_not_defined():
    p = DebugArghParser()

    assert run(p, '', {'raw_output': True}).out == p.format_usage()
    assert run(p, '').out == p.format_usage() + '\n'

    assert 'unrecognized arguments' in run(p, 'foo', exit=True)
    assert 'unrecognized arguments' in run(p, '--foo', exit=True)


def test_command_not_chosen():
    def cmd(args):
        return 1

    p = DebugArghParser()
    p.add_commands([cmd])

    if sys.version_info < (3,3):
        # Python before 3.3 exits with an error
        assert 'too few arguments' in run(p, '', exit=True)
    else:
        # Python since 3.3 returns a help message and doesn't exit
        assert 'usage:' in run(p, '').out


def test_invalid_choice():
    def cmd(args):
        return 1

    # root level command

    p = DebugArghParser()
    p.add_commands([cmd])

    assert 'invalid choice' in run(p, 'bar', exit=True)

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        assert 'too few arguments' in run(p, '--bar', exit=True)
    else:
        # Python since 3.3 exits with a more informative error
        assert run(p, '--bar', exit=True) == 'unrecognized arguments: --bar'

    # nested command

    p = DebugArghParser()
    p.add_commands([cmd], namespace='nest')

    assert 'invalid choice' in run(p, 'nest bar', exit=True)

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        assert 'too few arguments' in run(p, 'nest --bar', exit=True)
    else:
        # Python since 3.3 exits with a more informative error
        assert run(p, 'nest --bar', exit=True) == 'unrecognized arguments: --bar'


def test_unrecognized_arguments():
    def cmd():
        return 1

    # single-command parser

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '--bar', exit=True) == 'unrecognized arguments: --bar'
    assert run(p, 'bar', exit=True) == 'unrecognized arguments: bar'

    # multi-command parser

    p = DebugArghParser()
    p.add_commands([cmd])

    assert run(p, 'cmd --bar', exit=True) == 'unrecognized arguments: --bar'
    assert run(p, 'cmd bar', exit=True) == 'unrecognized arguments: bar'


def test_echo():
    "A simple command is resolved to a function."

    def echo(text):
        return 'you said {0}'.format(text)

    p = DebugArghParser()
    p.add_commands([echo])

    assert run(p, 'echo foo') == R(out='you said foo\n', err='')


def test_bool_action():
    "Action `store_true`/`store_false` is inferred from default value."

    def parrot(dead=False):
        return 'this parrot is no more' if dead else 'beautiful plumage'

    p = DebugArghParser()
    p.add_commands([parrot])

    assert run(p, 'parrot').out == 'beautiful plumage\n'
    assert run(p, 'parrot --dead').out == 'this parrot is no more\n'


def test_bare_namespace():
    "A command can be resolved to a function, not a namespace."

    def hello():
        return 'hello world'

    p = DebugArghParser()
    p.add_commands([hello], namespace='greet')

    # without arguments

    if sys.version_info < (3,3):
        # Python before 3.3 exits with an error
        assert run(p, 'greet', exit=True) == 'too few arguments'
    else:
        # Python since 3.3 returns a help message and doesn't exit
        assert 'usage:' in run(p, 'greet', exit=True).out

    # with an argument

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        message = 'too few arguments'
    else:
        # Python since 3.3 exits with a more informative error
        message = 'unrecognized arguments: --name=world'
    assert run(p, 'greet --name=world', exit=True) == message


def test_namespaced_function():
    "A subcommand is resolved to a function."

    def hello(name='world'):
        return 'Hello {0}!'.format(name or 'world')

    def howdy(buddy):
        return 'Howdy {0}?'.format(buddy)

    p = DebugArghParser()
    p.add_commands([hello, howdy], namespace='greet')

    assert run(p, 'greet hello').out == 'Hello world!\n'
    assert run(p, 'greet hello --name=John').out == 'Hello John!\n'
    assert run(p, 'greet hello John', exit=True) == 'unrecognized arguments: John'

    if sys.version_info < (3,3):
        # Python before 3.3 exits with a less informative error
        message = 'too few arguments'
    else:
        # Python since 3.3 exits with a more informative error
        message = 'the following arguments are required: buddy'

    assert message in run(p, 'greet howdy --name=John', exit=True)
    assert run(p, 'greet howdy John').out == 'Howdy John?\n'


def test_explicit_cmd_name():

    @argh.named('new-name')
    def orig_name():
        return 'ok'

    p = DebugArghParser()
    p.add_commands([orig_name])
    assert 'invalid choice' in run(p, 'orig-name', exit=True)
    assert run(p, 'new-name').out == 'ok\n'


def test_aliases():

    @argh.aliases('alias2', 'alias3')
    def alias1():
        return 'ok'

    p = DebugArghParser()
    p.add_commands([alias1])

    if argh.assembling.SUPPORTS_ALIASES:
        assert run(p, 'alias1').out == 'ok\n'
        assert run(p, 'alias2').out == 'ok\n'
        assert run(p, 'alias3').out == 'ok\n'


def test_help_alias():
    p = DebugArghParser()

    # assert the commands don't fail

    assert None == run(p, '--help', exit=True)
    assert None == run(p, 'greet --help', exit=True)
    assert None == run(p, 'greet hello --help', exit=True)

    assert None == run(p, 'help', exit=True)
    assert None == run(p, 'help greet', exit=True)
    assert None == run(p, 'help greet hello', exit=True)


def test_arg_order():
    """Positional arguments are resolved in the order in which the @arg
    decorators are defined.
    """
    def cmd(foo, bar):
        return foo, bar

    p = DebugArghParser()
    p.set_default_command(cmd)
    assert run(p, 'foo bar').out == 'foo\nbar\n'


def test_raw_output():
    "If the raw_output flag is set, no extra whitespace is added"

    def cmd(foo, bar):
        return foo, bar

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, 'foo bar').out == 'foo\nbar\n'
    assert run(p, 'foo bar', {'raw_output': True}).out == 'foobar'


def test_output_file():

    def cmd():
        return 'Hello world!'

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, '').out == 'Hello world!\n'
    assert run(p, '', {'output_file': None}).out == 'Hello world!\n'


def test_command_error():

    def whiner_plain():
        raise argh.CommandError('I feel depressed.')

    def whiner_iterable():
        yield 'Hello...'
        raise argh.CommandError('I feel depressed.')

    p = DebugArghParser()
    p.add_commands([whiner_plain, whiner_iterable])

    assert run(p, 'whiner-plain') == R(
        out='', err='CommandError: I feel depressed.\n')
    assert run(p, 'whiner-iterable') == R(
        out='Hello...\n', err='CommandError: I feel depressed.\n')


def test_custom_namespace():

    @argh.expects_obj
    def cmd(args):
        return args.custom_value

    p = DebugArghParser()
    p.set_default_command(cmd)
    namespace = argparse.Namespace()
    namespace.custom_value = 'foo'

    assert run(p, '', {'namespace': namespace}).out == 'foo\n'


def test_normalized_keys():
    """ Underscores in function args are converted to dashes and back.
    """
    def cmd(a_b):
        return a_b

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert run(p, 'hello').out == 'hello\n'


@mock.patch('argh.assembling.COMPLETION_ENABLED', True)
def test_custom_argument_completer():
    "Issue #33: Enable custom per-argument shell completion"

    @argh.arg('foo', completer='STUB')
    def func(foo):
        pass

    p = argh.ArghParser()
    p.set_default_command(func)

    assert p._actions[-1].completer == 'STUB'


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
            return value, 'w00t?'

        @staticmethod
        def static_meth2(value):
            return value, 'huh!'

    controller = Controller()

    p = DebugArghParser()
    p.add_commands([
        controller.instance_meth,
        controller.class_meth,
        controller.static_meth,
        Controller.static_meth2,
    ])

    assert run(p, 'instance-meth foo').out == 'foo\n123\n'
    assert run(p, 'class-meth foo').out == 'foo\n123\n'
    assert run(p, 'static-meth foo').out == 'foo\nw00t?\n'
    assert run(p, 'static-meth2 foo').out == 'foo\nhuh!\n'


def test_kwonlyargs():
    "Correct dispatch in presence of keyword-only arguments"
    if sys.version_info < (3,0):
        pytest.skip('unsupported configuration')

    ns = {}

    exec("""def cmd(*args, foo='1', bar, baz='3', **kwargs):
                return ' '.join(args), foo, bar, baz, len(kwargs)
         """, None, ns)
    cmd = ns['cmd']

    p = DebugArghParser()
    p.set_default_command(cmd)

    assert (run(p, '--baz=done test  this --bar=do').out ==
            'test this\n1\ndo\ndone\n0\n')
    if sys.version_info < (3,3):
        message = 'argument --bar is required'
    else:
        message = 'the following arguments are required: --bar'
    assert run(p, 'test --foo=do', exit=True) == message


def test_default_arg_values_in_help():
    "Argument defaults should appear in the help message implicitly"

    @argh.arg('name', default='Basil')
    @argh.arg('--task', default='hang the Moose')
    @argh.arg('--note', help='why is it a remarkable animal?')
    def remind(name, task=None, reason='there are creatures living in it',
               note='it can speak English'):
        return "Oh what is it now, can't you leave me in peace..."

    p = DebugArghParser()
    p.set_default_command(remind)

    assert 'Basil' in p.format_help()
    assert 'Moose' in p.format_help()
    assert 'creatures' in p.format_help()

    # explicit help message is not obscured by the implicit one...
    assert 'remarkable animal' in p.format_help()
    # ...but is still present
    assert 'it can speak' in p.format_help()


def test_default_arg_values_in_help__regression():
    "Empty string as default value → empty help string → broken argparse"

    def foo(bar=''):
        return bar

    p = DebugArghParser()
    p.set_default_command(foo)

    # doesn't break
    p.format_help()

    # now check details
    assert "-b BAR, --bar BAR  ''" in p.format_help()
    # note the empty str repr ^^^


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
        return 'hello'

    p = DebugArghParser()
    p.set_default_command(func)

    assert func.__doc__ in p.format_help()


def test_prog():
    "Program name propagates from sys.argv[0]"

    def cmd(foo=1):
        return foo

    p = DebugArghParser()
    p.add_commands([cmd])

    usage = get_usage_string()

    with iocapture.capture() as captured:
        assert run(p, '-h', exit=True) == None
        assert captured.stdout.startswith(usage)


def test_unknown_args():

    def cmd(foo=1):
        return foo

    p = DebugArghParser()
    p.set_default_command(cmd)

    get_usage_string('[-f FOO]')

    assert run(p, '--foo 1') == R(out='1\n', err='')
    assert run(p, '--bar 1', exit=True) == 'unrecognized arguments: --bar 1'
    assert run(p, '--bar 1', exit=False,
               kwargs={'skip_unknown_args': True}) == R(out='1\n', err='')
