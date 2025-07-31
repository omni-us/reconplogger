# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

os.environ["SPHINX_BUILD"] = ""


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "reconplogger"
copyright = "2018-present, omni:us"
author = "omni:us"


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "autodocsumm",
    "sphinx_autodoc_typehints",
]

templates_path = []
exclude_patterns = ["_build"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = []


# -- autodoc

sys.path.insert(0, os.path.abspath("../"))

autodoc_default_options = {
    "members": True,
    "exclude-members": "groups",
    "member-order": "bysource",
    "show-inheritance": True,
    "autosummary": True,
    "autosummary-imported-members": False,
    "special-members": "__init__,__call__",
}


# -- intersphinx

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
