#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018-2020 releng-tool

import os
import sys

# common
master_doc = 'index'

# meta
project = 'releng-tool'
copyright = '2020 releng-tool'
author = 'releng-tool'

# sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]

# add root for autodoc documentation
doc_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.dirname(doc_dir)
sys.path.insert(0, root_dir)

# output - html
html_theme = 'furo'
html_theme_options = {
    'navigation_with_keys': True,
}
html_static_path = ['_static']
html_show_copyright = False
html_show_sourcelink = False
html_show_sphinx = True


def setup(app):
    app.add_css_file('theme_overrides.css')
