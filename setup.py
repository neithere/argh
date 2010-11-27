#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Argh is a simple argparse wrapper.
#    Copyright © 2010  Andrey Mikhaylenko
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
from setuptools import setup
from _version import version


readme = open(os.path.join(os.path.dirname(__file__), 'README')).read()

setup(
    # overview
    name             = 'argh',
    description      = 'A simple argparse wrapper.',
    long_description = readme,

    # technical info
    version  = version,
    packages = ['argh'],
    requires = ['python (>= 2.5)', 'argparse (>=1.1)'],
    provides = ['argh'],

    # copyright
    author   = 'Andrey Mikhaylenko',
    author_email = 'andy@neithere.net',
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

    # release sanity check
    test_suite = 'nose.collector',
)
