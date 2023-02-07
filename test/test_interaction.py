# coding: utf-8
"""
Interaction Tests
~~~~~~~~~~~~~~~~~
"""
import sys
try:
    import unittest.mock as mock
except ImportError:
    # FIXME: remove in v.0.28
    import mock

import argh


def parse_choice(choice, **kwargs):
    argh.io._input = lambda prompt: choice
    return argh.confirm('test', **kwargs)


def test_simple():
    assert None == parse_choice('')
    assert None == parse_choice('', default=None)
    assert True == parse_choice('', default=True)
    assert False == parse_choice('', default=False)

    assert True == parse_choice('y')
    assert True == parse_choice('y', default=True)
    assert True == parse_choice('y', default=False)
    assert True == parse_choice('y', default=None)

    assert False == parse_choice('n')
    assert False == parse_choice('n', default=True)
    assert False == parse_choice('n', default=False)
    assert False == parse_choice('n', default=None)

    assert None == parse_choice('x') == None


def test_prompt():
    "Prompt is properly formatted"
    prompts = []

    def raw_input_mock(prompt):
        prompts.append(prompt)
    argh.io._input = raw_input_mock

    argh.confirm('do smth')
    assert prompts[-1] == 'do smth? (y/n)'

    argh.confirm('do smth', default=None)
    assert prompts[-1] == 'do smth? (y/n)'

    argh.confirm('do smth', default=True)
    assert prompts[-1] == 'do smth? (Y/n)'

    argh.confirm('do smth', default=False)
    assert prompts[-1] == 'do smth? (y/N)'


def test_encoding():
    "Unicode is accepted as prompt message"
    raw_input_mock = mock.MagicMock()

    argh.io._input = raw_input_mock

    msg = 'привет'
    if sys.version_info <= (3,0):
        msg = msg.decode('utf-8')

    argh.confirm(msg)

    # bytes in Python 2.x, Unicode in Python 3.x
    raw_input_mock.assert_called_once_with('привет? (y/n)')
