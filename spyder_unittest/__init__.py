# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Spyder Project Developers
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Spyder unitest plugin."""

# Local imports
from .unittestplugin import UnitTestPlugin as PLUGIN_CLASS

VERSION_INFO = (0, 1, 'b1')
__version__ = '.'.join(map(str, VERSION_INFO))
PLUGIN_CLASS
