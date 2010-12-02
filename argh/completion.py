# -*- coding: utf-8 -*-
"""
Shell completion
================

... warning::

    TODO: describe how to install

"""
import sys
import os

from argh.utils import get_subparsers


__all__ = ['autocomplete']


def autocomplete(root_parser):
    if not os.environ.get('ARGH_AUTO_COMPLETE'):
        return

    cwords = os.environ['COMP_WORDS'].split()[1:]
    cword = int(os.environ['COMP_CWORD'])  # XXX do we need this at all?

    choices = _autocomplete(root_parser, cwords, cword)

    print ' '.join(choices)

    sys.exit(1)

def _autocomplete(root_parser, cwords, cword):

    def _collect_choices(parser, word):
        for a in parser._actions:
            if a.choices:
                for choice in a.choices:
                    if word:
                        if choice.startswith(word):
                            yield choice
                    else:
                        yield choice

    choices = []

    # dig into the tree of parsers until we can yield no more choices

    # 1 ['']                      root parser  -> 'help fixtures'
    # 2 ['', 'fi']                root parser  -> 'fixtures'
    # 2 ['', 'fixtures']          subparser    -> 'load dump'
    # 3 ['', 'fixtures', 'lo']    subparser    -> 'load'
    # 3 ['', 'fixtures', 'load']  subparser    -> ''

    parser = root_parser
    choices = _collect_choices(parser, '')
    for word in cwords:
        # find the subparser and switch to it
        subparsers = get_subparsers(parser)
        if not subparsers:
            break
        if word in subparsers.choices:
            parser = subparsers.choices[word]
            word = ''
        choices = _collect_choices(parser, word)

    return choices
