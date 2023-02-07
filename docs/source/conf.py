# Configuration file for the Sphinx documentation builder.
import os
import sys

# -- Project information

project = u'argh'
copyright = u'2010—2023, Andrey Mikhaylenko'
author = 'Andrey Mikhaylenko'

# TODO: replace with getting the version via sphinx-pyproject
release = '0.28'
version = '0.28.0'

# -- General configuration

# let autodoc discover the module
sys.path.insert(0, os.path.abspath('../../src'))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.coverage']

templates_path = ['_templates']

html_theme = 'sphinx_rtd_theme'
