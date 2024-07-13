"""
Unit Tests For Autocompletion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from unittest.mock import patch

import argh


@patch("argh.completion.COMPLETION_ENABLED", True)
@patch("argh.completion.argcomplete")
def test_enabled(mock_argcomplete):
    parser = argh.ArghParser()

    parser.autocomplete()

    mock_argcomplete.autocomplete.assert_called_with(parser)


@patch("argh.completion.COMPLETION_ENABLED", False)
@patch("argh.completion.argcomplete")
@patch("argh.completion.os.getenv")
@patch("argh.completion.logger")
def test_disabled_without_bash(mock_logger, mock_getenv, mock_argcomplete):
    mock_getenv.return_value = "/bin/sh"
    parser = argh.ArghParser()

    parser.autocomplete()

    mock_argcomplete.assert_not_called()
    mock_logger.debug.assert_not_called()


@patch("argh.completion.COMPLETION_ENABLED", False)
@patch("argh.completion.argcomplete")
@patch("argh.completion.os.getenv")
@patch("argh.completion.logger")
def test_disabled_with_bash(mock_logger, mock_getenv, mock_argcomplete):
    mock_getenv.return_value = "/bin/bash"
    parser = argh.ArghParser()

    parser.autocomplete()

    mock_argcomplete.assert_not_called()
    mock_getenv.assert_called_with("SHELL", "")
    mock_logger.debug.assert_called_with(
        "Bash completion is not available. Please install argcomplete."
    )
