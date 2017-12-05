# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestgui.py."""

# Third party imports
from qtpy.QtCore import Qt

# Local imports
from spyder_unittest.backend.runnerbase import Category, TestResult
from spyder_unittest.widgets.datatree import COLORS, TestDataModel


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


def test_testdatamodel_data_background():
    model = TestDataModel()
    res = [TestResult(Category.OK, 'status', 'bar', 'foo'),
           TestResult(Category.FAIL, 'error', 'bar', 'foo', 'kadoom')]
    model.testresults = res
    index = model.index(0, 0)
    assert model.data(index, Qt.BackgroundRole) == COLORS[Category.OK]
    index = model.index(1, 2)
    assert model.data(index, Qt.BackgroundRole) == COLORS[Category.FAIL]


def test_testdatamodel_add_tests(qtbot):
    model = TestDataModel()
    assert model.testresults == []

    result1 = TestResult(Category.OK, 'status', 'bar', 'foo')
    with qtbot.waitSignal(model.rowsInserted) as blocker:
        model.add_testresults([result1])
    assert not blocker.args[0].isValid()  # args[0] is parent
    assert blocker.args[1] == 0  # args[1] is begin
    assert blocker.args[2] == 0  # args[2] is end
    assert model.testresults == [result1]

    result2 = TestResult(Category.FAIL, 'error', 'bar', 'foo', 'kadoom')
    with qtbot.waitSignal(model.rowsInserted) as blocker:
        model.add_testresults([result2])
    assert not blocker.args[0].isValid()
    assert blocker.args[1] == 1
    assert blocker.args[2] == 1
    assert model.testresults == [result1, result2]


def test_testdatamodel_replace_tests(qtbot):
    model = TestDataModel()
    result1 = TestResult(Category.OK, 'status', 'bar', 'foo')
    model.testresults = [result1]
    result2 = TestResult(Category.FAIL, 'error', 'bar', 'foo', 'kadoom')
    with qtbot.waitSignal(model.dataChanged) as blocker:
        model.update_testresults([result2])
    assert blocker.args[0].row() == 0  # args[0] is topLeft
    assert blocker.args[0].column() == 0
    assert not blocker.args[0].parent().isValid()
    assert blocker.args[1].row() == 0  # args[1] is bpttpmRight
    assert blocker.args[1].column() == 3
    assert not blocker.args[1].parent().isValid()
    assert blocker.args[2] == [Qt.DisplayRole]
    assert model.testresults == [result2]
