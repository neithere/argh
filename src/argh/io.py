# coding: utf-8
#
#  Copyright © 2010—2023 Andrey Mikhaylenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README.rst for copying conditions.
#
"""
Output Processing
~~~~~~~~~~~~~~~~~
"""
__all__ = ['safe_input']


def _input(prompt):
    # this function can be mocked up in tests
    return input(prompt)


def safe_input(prompt):
    """
    Prompts user for input. Correctly handles prompt message encoding.
    """
    if not isinstance(prompt, str):
        prompt = prompt.decode()

    return _input(prompt)
