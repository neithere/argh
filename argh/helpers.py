# -*- coding: utf-8 -*-
#
#  Copyright (c) 2010—2013 Andrey Mikhaylenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README for copying conditions.
#
"""
Helpers
~~~~~~~
"""
import argparse

from argh.completion import autocomplete
from argh.assembling import add_commands, set_default_command
from argh.dispatching import dispatch


__all__ = ['ArghParser']


class ArghParser(argparse.ArgumentParser):
    """ A subclass of :class:`ArgumentParser` with a couple of convenience
    methods.

    There is actually no need to subclass the parser. The methods are but
    wrappers for stand-alone functions :func:`~argh.assembling.add_commands`,
    :func:`~argh.completion.autocomplete` and
    :func:`~argh.dispatching.dispatch`.
    """
    def set_default_command(self, *args, **kwargs):
        "Wrapper for :func:`set_default_command`."
        return set_default_command(self, *args, **kwargs)

    def add_commands(self, *args, **kwargs):
        "Wrapper for :func:`add_commands`."
        return add_commands(self, *args, **kwargs)

    def autocomplete(self):
        return autocomplete(self)

    def dispatch(self, *args, **kwargs):
        "Wrapper for :func:`dispatch`."
        return dispatch(self, *args, **kwargs)
