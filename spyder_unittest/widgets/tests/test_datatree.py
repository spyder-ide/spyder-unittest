# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestgui.py."""

# Third party imports
from pytestqt import qtbot
from qtpy.QtCore import Qt

# Local imports
from spyder_unittest.backend.runnerbase import Category, TestResult
from spyder_unittest.widgets.datatree import DataTree

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


def test_unittestdatatree_shows_short_name_in_table(qtbot):
    datatree = DataTree()
    res = TestResult(Category.OK, 'status', 'bar', 'foo', '', 0, '')
    datatree.testresults = [res]
    datatree.populate_tree()
    assert datatree.topLevelItem(0).data(1, Qt.DisplayRole) == 'bar'


def test_unittestdatatree_shows_full_name_in_tooltip(qtbot):
    datatree = DataTree()
    res = TestResult(Category.OK, 'status', 'bar', 'foo', '', 0, '')
    datatree.testresults = [res]
    datatree.populate_tree()
    assert datatree.topLevelItem(0).data(1, Qt.ToolTipRole) == 'foo.bar'
