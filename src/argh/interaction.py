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
Interaction
~~~~~~~~~~~
"""

from typing import Optional

__all__ = ["confirm"]


MAX_CONFIRM_ITERATIONS = 3


def confirm(
    action: str, default: Optional[bool] = None, skip: bool = False
) -> Optional[bool]:
    """
    A shortcut for typical confirmation prompt.

    :param action:

        a string describing the action, e.g. "Apply changes". A question mark
        will be appended.

    :param default:

        `bool` or `None`. Determines what happens when user hits :kbd:`Enter`
        without typing in a choice. If `True`, default choice is "yes". If
        `False`, it is "no". If `None`, the prompt keeps reappearing until user
        types in a choice (not necessarily acceptable) or until the number of
        iteration reaches the limit. Default is `None`.

    :param skip:

        `bool`; if `True`, no interactive prompt is used and default choice is
        returned (useful for batch mode). Default is `False`.

    Usage::

        def delete(key, *, silent=False):
            item = db.get(Item, args.key)
            if confirm(f"Delete {item.title}", default=True, skip=silent):
                item.delete()
                print("Item deleted.")
            else:
                print("Operation cancelled.")

    Returns `None` on `KeyboardInterrupt` event.
    """
    if skip:
        return default

    # marking the default value with a capital letter
    defaults = {
        None: ("y", "n"),
        True: ("Y", "n"),
        False: ("y", "N"),
    }
    label_yes, label_no = defaults[default]
    prompt = f"{action}? ({label_yes}/{label_no})"
    choice = None
    try:
        if default is None:
            cnt = 1
            while not choice and cnt < MAX_CONFIRM_ITERATIONS:
                choice = input(prompt)
                cnt += 1
        else:
            choice = input(prompt)
    except KeyboardInterrupt:
        return None

    if choice in ("yes", "y", "Y"):
        return True
    if choice in ("no", "n", "N"):
        return False
    if default is not None:
        return default
    return None
