# Configuration file for the Sphinx documentation builder.
from datetime import date
import os
import sys


current_year = date.today().year

# -- Project information

project = 'argh'
copyright = f'2010—{current_year}, Andrey Mikhaylenko'
author = 'Andrey Mikhaylenko'

# TODO: replace with getting the version via sphinx-pyproject
release = '0.28'
version = '0.28.0'

# -- General configuration

# let autodoc discover the module
sys.path.insert(0, os.path.abspath('../../src'))

master_doc = 'index'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']

html_theme = 'sphinx_rtd_theme'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

nitpicky = True
