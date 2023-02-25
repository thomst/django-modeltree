# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))
from modeltree.__version__ import __version__

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'django-modeltree'
copyright = '2023, Thomas Leichtfuß'
author = 'Thomas Leichtfuß'
version = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinxcontrib.napoleon',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# autodoc-configuration
autoclass_content = 'both'
autodoc_member_order = 'bysource'

# intersphinx-config
intersphinx_mapping = {
    'django': ('https://docs.djangoproject.com/en/dev/', 'http://docs.djangoproject.com/en/dev/_objects/'),
    'anytree': ('https://anytree.readthedocs.io/en/latest/', 'https://anytree.readthedocs.io/en/latest/objects.inv'),
    }
