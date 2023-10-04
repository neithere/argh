"""
Dispatching tests
~~~~~~~~~~~~~~~~~
"""
import argparse
import io
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
    mock_set_default_command.assert_called_with(mock_parser, func)
    mock_dispatch.assert_called_with(mock_parser)


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
    mock_add_commands.assert_called_with(mock_parser, [func])
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
