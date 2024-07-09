"""Configuration file for the Sphinx documentation builder."""

import os
import sys
from datetime import date

from sphinx_pyproject import SphinxConfig

current_year = date.today().year

config = SphinxConfig("../pyproject.toml")

# -- Project information

project = config.name
author = config.author
copyright = f"2010—{current_year}, {author}"
version = config.version
release = version

# -- General configuration

# let autodoc discover the module
sys.path.insert(0, os.path.abspath("../../src"))

master_doc = "index"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]

html_theme = "sphinx_rtd_theme"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

nitpicky = True

autodoc_typehints = "both"
