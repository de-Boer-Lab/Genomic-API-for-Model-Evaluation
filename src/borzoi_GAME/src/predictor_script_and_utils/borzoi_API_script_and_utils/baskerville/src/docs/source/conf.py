# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

# This root should be where docs folder is visible.
sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../../baskerville"))
sys.path.insert(0, os.path.abspath("../../baskerville/scripts"))
sys.path.insert(0, os.path.abspath("../../bashkerville/helpers"))

sys.setrecursionlimit(1500)

project = "baskerville"
copyright = "2023, David Kelly"
author = "David Kelly"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.githubpages",
    "sphinxcontrib.apidoc",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
