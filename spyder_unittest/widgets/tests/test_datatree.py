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
    res = [TestResult(Category.OK, 'status', 'foo.bar'),
           TestResult(Category.FAIL, 'error', 'foo.bar', 'kadoom', 0,
                      'crash!\nboom!')]
    model.testresults = res
    qtmodeltester.check(model)


def test_testdatamodel_shows_abbreviated_name_in_table(qtbot):
    model = TestDataModel()
    res = TestResult(Category.OK, 'status', 'foo.bar', '', 0, '')
    model.testresults = [res]
    index = model.index(0, 1)
    assert model.data(index, Qt.DisplayRole) == 'f.bar'


def test_testdatamodel_shows_full_name_in_tooltip(qtbot):
    model = TestDataModel()
    res = TestResult(Category.OK, 'status', 'foo.bar', '', 0, '')
    model.testresults = [res]
    index = model.index(0, 1)
    assert model.data(index, Qt.ToolTipRole) == 'foo.bar'


def test_testdatamodel_data_background():
    model = TestDataModel()
    res = [TestResult(Category.OK, 'status', 'foo.bar'),
           TestResult(Category.FAIL, 'error', 'foo.bar', 'kadoom')]
    model.testresults = res
    index = model.index(0, 0)
    assert model.data(index, Qt.BackgroundRole) == COLORS[Category.OK]
    index = model.index(1, 2)
    assert model.data(index, Qt.BackgroundRole) == COLORS[Category.FAIL]


def test_testdatamodel_add_tests(qtbot):
    def check_args1(parent, begin, end):
        return not parent.isValid() and begin == 0 and end == 0

    def check_args2(parent, begin, end):
        return not parent.isValid() and begin == 1 and end == 1

    model = TestDataModel()
    assert model.testresults == []

    result1 = TestResult(Category.OK, 'status', 'foo.bar')
    with qtbot.waitSignals([model.rowsInserted, model.sig_summary],
                           check_params_cbs=[check_args1, None],
                           raising=True):
        model.add_testresults([result1])
    assert model.testresults == [result1]

    result2 = TestResult(Category.FAIL, 'error', 'foo.bar', 'kadoom')
    with qtbot.waitSignals([model.rowsInserted, model.sig_summary],
                           check_params_cbs=[check_args2, None],
                           raising=True):
        model.add_testresults([result2])
    assert model.testresults == [result1, result2]


def test_testdatamodel_replace_tests(qtbot):
    def check_args(topLeft, bottomRight, *args):
        return (topLeft.row() == 0
                and topLeft.column() == 0
                and not topLeft.parent().isValid()
                and bottomRight.row() == 0
                and bottomRight.column() == 3
                and not bottomRight.parent().isValid())

    model = TestDataModel()
    result1 = TestResult(Category.OK, 'status', 'foo.bar')
    model.testresults = [result1]
    result2 = TestResult(Category.FAIL, 'error', 'foo.bar', 'kadoom')
    with qtbot.waitSignals([model.dataChanged, model.sig_summary],
                           check_params_cbs=[check_args, None],
                           raising=True):
        model.update_testresults([result2])
    assert model.testresults == [result2]
