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
__all__ = ["safe_input"]


def safe_input(prompt):  # pragma: no cover
    """
    .. deprecated:: 0.28

        This function will be removed in Argh v.0.30.
        Please use the built-in function `input()` instead.

    """
    if not isinstance(prompt, str):
        prompt = prompt.decode()

    return input(prompt)
