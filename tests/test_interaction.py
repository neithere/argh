# coding: utf-8
"""
Interaction Tests
~~~~~~~~~~~~~~~~~
"""
import unittest.mock as mock

import argh


def parse_choice(choice, **kwargs):
    argh.io._input = lambda prompt: choice
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

    argh.io._input = raw_input_mock

    argh.confirm("do smth")
    assert prompts[-1] == "do smth? (y/n)"

    argh.confirm("do smth", default=None)
    assert prompts[-1] == "do smth? (y/n)"

    argh.confirm("do smth", default=True)
    assert prompts[-1] == "do smth? (Y/n)"

    argh.confirm("do smth", default=False)
    assert prompts[-1] == "do smth? (y/N)"


def test_encoding():
    "Unicode is accepted as prompt message"
    raw_input_mock = mock.MagicMock()

    argh.io._input = raw_input_mock

    msg = "привет"

    argh.confirm(msg)

    raw_input_mock.assert_called_once_with("привет? (y/n)")
