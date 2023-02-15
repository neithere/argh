"""
Dispatching tests
~~~~~~~~~~~~~~~~~
"""
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
