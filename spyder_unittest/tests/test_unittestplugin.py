# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestplugin.py"""

# Third party imports
from qtpy.QtWidgets import QWidget
import pytest

# Local imports
from spyder_unittest.unittestplugin import UnitTestPlugin

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


@pytest.fixture
def plugin(qtbot):
    """Set up the unittest plugin."""
    res = UnitTestPlugin(None)
    qtbot.addWidget(res)
    res.main = Mock()
    res.main.run_menu_actions = [42]
    res.main.editor.pythonfile_dependent_actions = [42]
    res.register_plugin()
    return res


def test_initialization(plugin):
    """Check that plugin initialization does not yield an error."""
    plugin.show()
