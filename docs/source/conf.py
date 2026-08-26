# Configuration file for the Sphinx documentation builder.
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'GAME: Genomic API for Model Evaluation'
copyright = '2025, Ishika Luthra, Satyam Priyadarshi'
author = 'Ishika Luthra, Satyam Priyadarshi'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [    
    'sphinx.ext.autodoc',      # Read docstrings
    'sphinx.ext.napoleon',     # Support Google-style docstrings
    'sphinx.ext.viewcode',     # Link to source code
    'myst_parser',             # Support Markdown (README.md)
    'sphinx_book_theme',
    "sphinx_design",
    "sphinx_copybutton",
]
# Optional: enable MyST extensions
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "linkify",
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
