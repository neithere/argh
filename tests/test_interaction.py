"""
Interaction Tests
~~~~~~~~~~~~~~~~~
"""

import unittest.mock as mock

import argh


def parse_choice(choice, **kwargs):
    with mock.patch("argh.interaction.input", lambda prompt: choice):
        return argh.confirm("test", **kwargs)


def test_simple():
    assert parse_choice("") is None
    assert parse_choice("", default=None) is None
    assert parse_choice("", default=True) is True
    assert parse_choice("", default=False) is False

    assert parse_choice("y") is True
    assert parse_choice("y", default=True) is True
    assert parse_choice("y", default=False) is True
    assert parse_choice("y", default=None) is True

    assert parse_choice("n") is False
    assert parse_choice("n", default=True) is False
    assert parse_choice("n", default=False) is False
    assert parse_choice("n", default=None) is False

    assert parse_choice("x") is None


def test_prompt():
    "Prompt is properly formatted"
    prompts = []

    def raw_input_mock(prompt):
        prompts.append(prompt)

    with mock.patch("argh.interaction.input", raw_input_mock):
        argh.confirm("do smth")
        assert prompts[-1] == "do smth? (y/n)"

        argh.confirm("do smth", default=None)
        assert prompts[-1] == "do smth? (y/n)"

        argh.confirm("do smth", default=True)
        assert prompts[-1] == "do smth? (Y/n)"

        argh.confirm("do smth", default=False)
        assert prompts[-1] == "do smth? (y/N)"


@mock.patch("argh.interaction.input")
def test_encoding(mock_input):
    "Unicode is accepted as prompt message"

    msg = "привет"

    argh.confirm(msg)

    mock_input.assert_called_once_with("привет? (y/n)")


@mock.patch("argh.interaction.input")
def test_skip(mock_input):
    retval = argh.confirm("test", default=123, skip=True)

    assert retval == 123
    mock_input.assert_not_called()


@mock.patch("argh.interaction.input")
def test_keyboard_interrupt(mock_input):
    mock_input.side_effect = KeyboardInterrupt
    retval = argh.confirm("test")
    assert retval is None
