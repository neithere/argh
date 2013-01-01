#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Argh is a simple argparse wrapper.
#    Copyright © 2010—2013  Andrey Mikhaylenko
#
#    This file is part of Argh.
#
#    Argh is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Argh is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with Argh.  If not, see <http://gnu.org/licenses/>.


import os

# Why distutils?
#
# We could bundle distribute_setup.py and call it as recommended:
#   http://packages.python.org/distribute/using.html
# However, `distribute` seems to break PyPy (at least 1.6 thru 1.9).
# So we'll simply fall back to plain distutils.
try:
    from setuptools import setup
except:
    from distutils.core import setup

# Importing `__version__` from `argh` would trigger a cascading import
# of `argparse`. We need to avoid this as Python < 2.7 ships without argparse.
__version__ = None
with open('argh/__init__.py') as f:
    for line in f:
        if line.startswith('__version__'):
            exec(line)
            break
assert __version__, 'argh.__version__ must be imported correctly'


readme = open(os.path.join(os.path.dirname(__file__), 'README')).read()


setup(
    # overview
    name             = 'argh',
    description      = 'An unobtrusive argparse wrapper with natural syntax',
    long_description = readme,

    # technical info
    version  = __version__,
    packages = ['argh'],
    provides = ['argh'],
    requires = ['python(>=2.6)', 'argparse(>=1.1)'],
    install_requires = ['argparse>=1.1'],    # for Python 2.6 (no bundled argparse; setuptools is likely to exist)

    # copyright
    author   = 'Andrey Mikhaylenko',
    author_email = 'neithere@gmail.com',
    license  = 'GNU Lesser General Public License (LGPL), Version 3',

    # more info
    url          = 'http://bitbucket.org/neithere/argh/',
    download_url = 'http://bitbucket.org/neithere/argh/src/',

    # categorization
    keywords     = ('cli command line argparse optparse argument option'),
    classifiers  = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
