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
from spyder_unittest.widgets.datatree import TestDataModel

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


def test_testdatamodel_using_qtmodeltester(qtmodeltester):
    model = TestDataModel()
    res = [TestResult(Category.OK, 'status', 'bar', 'foo'),
           TestResult(Category.FAIL, 'error', 'bar', 'foo', 'kadoom', 0,
                      'crash!\nboom!')]
    model.testresults = res
    qtmodeltester.check(model)


def test_testdatamodel_shows_short_name_in_table(qtbot):
    model = TestDataModel()
    res = TestResult(Category.OK, 'status', 'bar', 'foo', '', 0, '')
    model.testresults = [res]
    index = model.index(0, 1)
    assert model.data(index, Qt.DisplayRole) == 'bar'


def test_testdatamodel_shows_full_name_in_tooltip(qtbot):
    model = TestDataModel()
    res = TestResult(Category.OK, 'status', 'bar', 'foo', '', 0, '')
    model.testresults = [res]
    index = model.index(0, 1)
    assert model.data(index, Qt.ToolTipRole) == 'foo.bar'
