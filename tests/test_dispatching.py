"""
Dispatching tests
~~~~~~~~~~~~~~~~~
"""

import argparse
import errno
import io
import os
import subprocess
import sys
from unittest.mock import Mock, patch

import pytest

import argh


def _dispatch_and_capture(func, command_string, **kwargs):
    if hasattr(command_string, "split"):
        args = command_string.split()
    else:
        args = command_string

    _io = io.StringIO()
    if "output_file" not in kwargs:
        kwargs["output_file"] = _io

    result = argh.dispatch_command(func, args, **kwargs)

    if kwargs.get("output_file") is None:
        return result
    else:
        _io.seek(0)
        return _io.read()


def run_func(func, command_string, **kwargs):
    try:
        result = _dispatch_and_capture(func, command_string, **kwargs)
    except SystemExit:
        raise
    else:
        return result


@patch("argh.dispatching.argparse.ArgumentParser")
@patch("argh.dispatching.dispatch")
@patch("argh.dispatching.set_default_command")
def test_dispatch_command(mock_set_default_command, mock_dispatch, mock_parser_class):
    def func():
        pass

    argh.dispatching.dispatch_command(func)

    mock_parser_class.assert_called_once()
    mock_parser = mock_parser_class.return_value
    mock_set_default_command.assert_called_with(
        mock_parser,
        func,
        name_mapping_policy=argh.assembling.NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
    )
    mock_dispatch.assert_called_with(mock_parser)


@pytest.mark.parametrize("always_flush", [True, False])
def test_run_endpoint_function__always_flush(always_flush):
    def func():
        return ["first line", "second line"]

    out_io = Mock(spec=io.StringIO)

    argh.dispatching.run_endpoint_function(
        func, argparse.Namespace(), output_file=out_io, always_flush=always_flush
    )

    if always_flush:
        assert out_io.flush.call_count == 2
    else:
        out_io.flush.assert_called_once_with()
    out_io.close.assert_not_called()


@pytest.mark.parametrize("close_fails", [False, True])
@pytest.mark.parametrize(
    "failure, raw_output",
    [("write", False), ("write", True), ("newline", False), ("flush", False)],
)
def test_broken_output_pipe(failure, raw_output, close_fails):
    produced = []

    def func():
        for line in ["first line", "second line"]:
            produced.append(line)
            yield line

    output = Mock(spec=io.StringIO)
    error = BrokenPipeError(errno.EPIPE, "Broken pipe")
    if failure == "write":
        output.write.side_effect = error
    elif failure == "newline":
        output.write.side_effect = [10, error]
    else:
        output.flush.side_effect = error
    if close_fails:
        output.close.side_effect = error
    errors = io.StringIO()

    assert (
        argh.dispatching.run_endpoint_function(
            func,
            argparse.Namespace(),
            output_file=output,
            errors_file=errors,
            raw_output=raw_output,
            always_flush=True,
        )
        is None
    )

    assert produced == ["first line"]
    assert errors.getvalue() == ""
    output.close.assert_called_once_with()


@pytest.mark.parametrize("close_fails", [False, True])
def test_broken_output_pipe_on_final_flush(close_fails):
    output = Mock(spec=io.StringIO)
    output.flush.side_effect = BrokenPipeError(errno.EPIPE, "Broken pipe")
    if close_fails:
        output.close.side_effect = BrokenPipeError(errno.EPIPE, "Broken pipe")

    argh.dispatching.run_endpoint_function(
        lambda: "buffered output", argparse.Namespace(), output_file=output
    )

    output.flush.assert_called_once_with()
    output.close.assert_called_once_with()


@pytest.mark.parametrize("operation", ["write", "flush"])
def test_other_output_errors_propagate(operation):
    output = Mock(spec=io.StringIO)
    error = OSError(errno.ENOSPC, "No space left on device")
    getattr(output, operation).side_effect = error

    with pytest.raises(OSError) as excinfo:
        argh.dispatching.run_endpoint_function(
            lambda: "output",
            argparse.Namespace(),
            output_file=output,
            always_flush=True,
        )

    assert excinfo.value is error
    output.close.assert_not_called()


@pytest.mark.parametrize("during_iteration", [False, True])
def test_command_broken_pipe_errors_propagate(during_iteration):
    error = BrokenPipeError(errno.EPIPE, "Command's own pipe failed")

    def func():
        if during_iteration:
            yield "first line"
        raise error

    output = io.StringIO()
    with pytest.raises(BrokenPipeError) as excinfo:
        argh.dispatching.run_endpoint_function(
            func, argparse.Namespace(), output_file=output
        )

    assert excinfo.value is error
    assert not output.closed


def test_result_string_conversion_errors_propagate():
    error = BrokenPipeError(errno.EPIPE, "Result conversion failed")

    class Result:
        def __str__(self):
            raise error

    with pytest.raises(BrokenPipeError) as excinfo:
        argh.dispatching.run_endpoint_function(
            Result, argparse.Namespace(), output_file=io.StringIO()
        )

    assert excinfo.value is error


@pytest.mark.parametrize("always_flush", [False, True])
@pytest.mark.parametrize("message_size", [1, 16384])
def test_closed_pipe_subprocess(always_flush, message_size):
    # A real closed pipe also checks that buffered data is not flushed again
    # during interpreter shutdown, which would print an ignored exception.
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import argh\n"
                f"argh.dispatch_command(lambda: 'x' * {message_size}, "
                f"always_flush={always_flush})\n",
            ],
            stdout=write_fd,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
    finally:
        os.close(write_fd)

    assert result.returncode == 0, result.stderr.decode()
    assert result.stderr == b""


@patch("argh.dispatching.parse_and_resolve")
@patch("argh.dispatching.run_endpoint_function")
def test_dispatch_command_two_stage(mock_run_endpoint_function, mock_parse_and_resolve):
    def func() -> str:
        return "function output"

    mock_parser = Mock(argparse.ArgumentParser)
    mock_parser.parse_args.return_value = argparse.Namespace(foo=123)
    argv = ["foo", "bar", "baz"]
    completion = False
    mock_output_file = Mock(io.TextIOBase)
    mock_errors_file = Mock(io.TextIOBase)
    raw_output = False
    skip_unknown_args = False
    always_flush = True
    mock_endpoint_function = Mock()
    mock_namespace = Mock(argparse.Namespace)
    mock_namespace_obj = Mock(argparse.Namespace)
    mock_parse_and_resolve.return_value = (mock_endpoint_function, mock_namespace_obj)
    mock_run_endpoint_function.return_value = "run_endpoint_function retval"

    retval = argh.dispatching.dispatch(
        parser=mock_parser,
        argv=argv,
        completion=completion,
        namespace=mock_namespace,
        skip_unknown_args=skip_unknown_args,
        output_file=mock_output_file,
        errors_file=mock_errors_file,
        raw_output=raw_output,
        always_flush=always_flush,
    )

    mock_parse_and_resolve.assert_called_with(
        parser=mock_parser,
        argv=argv,
        completion=completion,
        namespace=mock_namespace,
        skip_unknown_args=skip_unknown_args,
    )
    mock_run_endpoint_function.assert_called_with(
        function=mock_endpoint_function,
        namespace_obj=mock_namespace_obj,
        output_file=mock_output_file,
        errors_file=mock_errors_file,
        raw_output=raw_output,
        always_flush=always_flush,
    )
    assert retval == "run_endpoint_function retval"


@patch("argh.dispatching.argparse.ArgumentParser")
@patch("argh.dispatching.dispatch")
@patch("argh.dispatching.add_commands")
def test_dispatch_commands(mock_add_commands, mock_dispatch, mock_parser_class):
    def func():
        pass

    argh.dispatching.dispatch_commands([func])

    mock_parser_class.assert_called_once()
    mock_parser = mock_parser_class.return_value
    mock_add_commands.assert_called_with(
        mock_parser,
        [func],
        name_mapping_policy=argh.assembling.NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
    )
    mock_dispatch.assert_called_with(mock_parser)


@patch("argh.dispatching.dispatch")
@patch("argh.dispatching.add_commands")
@patch("argparse.ArgumentParser")
def test_entrypoint(ap_cls_mock, add_commands_mock, dispatch_mock):
    entrypoint = argh.EntryPoint("my cool app")

    # no commands

    with pytest.raises(argh.exceptions.DispatchingError) as excinfo:
        entrypoint()
    assert excinfo.exconly().endswith(
        'DispatchingError: no commands for entry point "my cool app"'
    )

    mocked_parser = Mock()
    ap_cls_mock.return_value = mocked_parser

    # a single command

    @entrypoint
    def greet():
        return "hello"

    entrypoint()

    assert add_commands_mock.called
    add_commands_mock.assert_called_with(mocked_parser, [greet])
    assert dispatch_mock.called
    dispatch_mock.assert_called_with(mocked_parser)

    # multiple commands

    add_commands_mock.reset_mock()
    dispatch_mock.reset_mock()

    @entrypoint
    def hit():
        return "knight with a chicken"

    entrypoint()

    assert add_commands_mock.called
    add_commands_mock.assert_called_with(mocked_parser, [greet, hit])
    assert dispatch_mock.called
    dispatch_mock.assert_called_with(mocked_parser)


@patch("argh.dispatching.dispatch")
@patch("argh.dispatching.set_default_command")
@patch("argparse.ArgumentParser")
def test_dispatch_command_naming_policy(
    parser_cls_mock, set_default_command_mock, dispatch_mock
):
    def func(): ...

    parser_mock = Mock()
    parser_cls_mock.return_value = parser_mock

    argh.dispatching.dispatch_command(func)
    set_default_command_mock.assert_called_with(
        parser_mock,
        func,
        name_mapping_policy=argh.assembling.NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
    )
    set_default_command_mock.reset_mock()

    argh.dispatching.dispatch_command(func, old_name_mapping_policy=True)
    set_default_command_mock.assert_called_with(
        parser_mock,
        func,
        name_mapping_policy=argh.assembling.NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
    )
    set_default_command_mock.reset_mock()

    argh.dispatching.dispatch_command(func, old_name_mapping_policy=False)
    set_default_command_mock.assert_called_with(
        parser_mock,
        func,
        name_mapping_policy=argh.assembling.NameMappingPolicy.BY_NAME_IF_KWONLY,
    )


@patch("argh.dispatching.dispatch")
@patch("argh.dispatching.add_commands")
@patch("argparse.ArgumentParser")
def test_dispatch_commands_naming_policy(
    parser_cls_mock, add_commands_mock, dispatch_mock
):
    def func(): ...

    parser_mock = Mock()
    parser_cls_mock.return_value = parser_mock

    argh.dispatching.dispatch_commands(func)
    add_commands_mock.assert_called_with(
        parser_mock,
        func,
        name_mapping_policy=argh.assembling.NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
    )
    add_commands_mock.reset_mock()

    argh.dispatching.dispatch_commands(func, old_name_mapping_policy=True)
    add_commands_mock.assert_called_with(
        parser_mock,
        func,
        name_mapping_policy=argh.assembling.NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT,
    )
    add_commands_mock.reset_mock()

    argh.dispatching.dispatch_commands(func, old_name_mapping_policy=False)
    add_commands_mock.assert_called_with(
        parser_mock,
        func,
        name_mapping_policy=argh.assembling.NameMappingPolicy.BY_NAME_IF_KWONLY,
    )
