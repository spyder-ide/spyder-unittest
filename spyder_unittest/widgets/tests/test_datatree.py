# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestgui.py."""

# Third party imports
from qtpy.QtCore import QModelIndex, QPoint, Qt
from qtpy.QtGui import QContextMenuEvent
import pytest

# Local imports
from spyder_unittest.backend.runnerbase import Category, TestResult
from spyder_unittest.widgets.datatree import (COLORS, TestDataModel,
                                              TestDataView)

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


@pytest.fixture
def view_and_model(qtbot):
    view = TestDataView()
    model = TestDataModel()
    # setModel() before populating testresults because setModel() does a sort
    view.setModel(model)
    res = [TestResult(Category.OK, 'status', 'foo.bar'),
           TestResult(Category.FAIL, 'error', 'foo.bar', 'kadoom', 0,
                      'crash!\nboom!', filename='ham.py', lineno=42)]
    model.testresults = res
    return view, model

def test_contextMenuEvent_calls_exec(view_and_model, monkeypatch):
    # test that a menu is displayed when clicking on an item
    mock_exec = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.datatree.QMenu.exec_', mock_exec)
    view, model = view_and_model
    pos = view.visualRect(model.index(0, 0)).center()
    event = QContextMenuEvent(QContextMenuEvent.Mouse, pos)
    view.contextMenuEvent(event)
    assert mock_exec.called

    # test that no menu is displayed when clicking below the bottom item
    mock_exec.reset_mock()
    pos = view.visualRect(model.index(1, 0)).bottomRight()
    pos += QPoint(0, 1)
    event = QContextMenuEvent(QContextMenuEvent.Mouse, pos)
    view.contextMenuEvent(event)
    assert not mock_exec.called

def test_go_to_test_definition_with_invalid_target(view_and_model, qtbot):
    view, model = view_and_model
    with qtbot.assertNotEmitted(view.sig_edit_goto):
        view.go_to_test_definition(model.index(0, 0))

def test_go_to_test_definition_with_valid_target(view_and_model, qtbot):
    view, model = view_and_model
    with qtbot.waitSignal(view.sig_edit_goto) as blocker:
        view.go_to_test_definition(model.index(1, 0))
    assert blocker.args == ['ham.py', 42]

def test_go_to_test_definition_with_lineno_none(view_and_model, qtbot):
    view, model = view_and_model
    res = model.testresults
    res[1].lineno = None
    model.testresults = res
    with qtbot.waitSignal(view.sig_edit_goto) as blocker:
        view.go_to_test_definition(model.index(1, 0))
    assert blocker.args == ['ham.py', 0]

def test_make_index_canonical_with_index_in_column2(view_and_model):
    view, model = view_and_model
    index = model.index(1, 2)
    res = view.make_index_canonical(index)
    assert res == model.index(1, 0)

def test_make_index_canonical_with_level2_index(view_and_model):
    view, model = view_and_model
    index = model.index(1, 0, model.index(1, 0))
    res = view.make_index_canonical(index)
    assert res == model.index(1, 0)

def test_make_index_canonical_with_invalid_index(view_and_model):
    view, model = view_and_model
    index = QModelIndex()
    res = view.make_index_canonical(index)
    assert res is None

def test_build_context_menu(view_and_model):
    view, model = view_and_model
    menu = view.build_context_menu(model.index(0, 0))
    assert menu.actions()[0].text() == 'Expand'
    assert menu.actions()[1].text() == 'Go to definition'

def test_build_context_menu_with_disabled_entries(view_and_model):
    view, model = view_and_model
    menu = view.build_context_menu(model.index(0, 0))
    assert menu.actions()[0].isEnabled() == False
    assert menu.actions()[1].isEnabled() == False

def test_build_context_menu_with_enabled_entries(view_and_model):
    view, model = view_and_model
    menu = view.build_context_menu(model.index(1, 0))
    assert menu.actions()[0].isEnabled() == True
    assert menu.actions()[1].isEnabled() == True

def test_build_context_menu_with_expanded_entry(view_and_model):
    view, model = view_and_model
    view.expand(model.index(1, 0))
    menu = view.build_context_menu(model.index(1, 0))
    assert menu.actions()[0].text() == 'Collapse'
    assert menu.actions()[0].isEnabled() == True

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

def test_testdatamodel_data_userrole():
    model = TestDataModel()
    res = [TestResult(Category.OK, 'status', 'foo.bar', filename='somefile',
                      lineno=42)]
    model.testresults = res
    index = model.index(0, 0)
    assert model.data(index, Qt.UserRole) == ('somefile', 42)

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

STANDARD_TESTRESULTS = [
    TestResult(Category.OK, 'status', 'foo.bar', time=2),
    TestResult(Category.FAIL, 'failure', 'fu.baz', 'kaboom',time=1),
    TestResult(Category.FAIL, 'error', 'fu.bar', 'boom')]

def test_testdatamodel_sort_by_status_ascending(qtbot):
    model = TestDataModel()
    model.testresults = STANDARD_TESTRESULTS[:]
    with qtbot.waitSignal(model.dataChanged):
        model.sort(0, Qt.AscendingOrder)
    expected = [STANDARD_TESTRESULTS[k] for k in [2, 1, 0]]
    assert model.testresults == expected

def test_testdatamodel_sort_by_status_descending():
    model = TestDataModel()
    model.testresults = STANDARD_TESTRESULTS[:]
    model.sort(0, Qt.DescendingOrder)
    expected = [STANDARD_TESTRESULTS[k] for k in [0, 1, 2]]
    assert model.testresults == expected

def test_testdatamodel_sort_by_name():
    model = TestDataModel()
    model.testresults = STANDARD_TESTRESULTS[:]
    model.sort(1, Qt.AscendingOrder)
    expected = [STANDARD_TESTRESULTS[k] for k in [0, 2, 1]]
    assert model.testresults == expected

def test_testdatamodel_sort_by_message():
    model = TestDataModel()
    model.testresults = STANDARD_TESTRESULTS[:]
    model.sort(2, Qt.AscendingOrder)
    expected = [STANDARD_TESTRESULTS[k] for k in [0, 2, 1]]
    assert model.testresults == expected

def test_testdatamodel_sort_by_time():
    model = TestDataModel()
    model.testresults = STANDARD_TESTRESULTS[:]
    model.sort(3, Qt.AscendingOrder)
    expected = [STANDARD_TESTRESULTS[k] for k in [2, 1, 0]]
    assert model.testresults == expected
