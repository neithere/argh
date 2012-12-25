# -*- coding: utf-8 -*-
"""
Interaction Tests
~~~~~~~~~~~~~~~~~
"""
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
    "Unicode and bytes are accepted as prompt message"
    def raw_input_mock(prompt):
        if not argh.six.PY3:
            assert isinstance(prompt, argh.six.binary_type)
    argh.io._input = raw_input_mock
    argh.confirm(argh.six.u('привет'))
