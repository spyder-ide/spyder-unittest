# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestgui.py."""

# Standard library imports
import os

# Third party imports
from pytestqt import qtbot
from qtpy.QtCore import Qt
import pytest

# Local imports
from spyder_unittest.backend.runnerbase import Category, TestResult
from spyder_unittest.widgets.configdialog import Config
from spyder_unittest.widgets.unittestgui import (UnitTestDataTree,
                                                 UnitTestWidget)

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


def test_unittestdatatree_shows_short_name_in_table(qtbot):
    datatree = UnitTestDataTree()
    res = TestResult(Category.OK, 'status', 'bar', 'foo', '', 0, '')
    datatree.testresults = [res]
    datatree.populate_tree()
    assert datatree.topLevelItem(0).data(1, Qt.DisplayRole) == 'bar'


def test_unittestdatatree_shows_full_name_in_tooltip(qtbot):
    datatree = UnitTestDataTree()
    res = TestResult(Category.OK, 'status', 'bar', 'foo', '', 0, '')
    datatree.testresults = [res]
    datatree.populate_tree()
    assert datatree.topLevelItem(0).data(1, Qt.ToolTipRole) == 'foo.bar'


@pytest.mark.parametrize('framework', ['py.test', 'nose'])
def test_run_tests_and_display_results(qtbot, tmpdir, monkeypatch, framework):
    """Basic check."""
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath

    with open(testfilename, 'w') as f:
        f.write("def test_ok(): assert 1+1 == 2\n"
                "def test_fail(): assert 1+1 == 3\n")

    MockQMessageBox = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.unittestgui.QMessageBox',
                        MockQMessageBox)

    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=tmpdir.strpath, framework=framework)
    with qtbot.waitSignal(widget.sig_finished, timeout=10000, raising=True):
        widget.run_tests(config)

    MockQMessageBox.assert_not_called()
    dt = widget.datatree
    itemcount = dt.topLevelItemCount()
    assert itemcount == 2
    assert dt.topLevelItem(0).data(0, Qt.DisplayRole) == 'ok'
    assert dt.topLevelItem(0).data(1, Qt.DisplayRole) == 'test_ok'
    assert dt.topLevelItem(0).data(1, Qt.ToolTipRole) == 'test_foo.test_ok'
    assert dt.topLevelItem(0).data(2, Qt.DisplayRole) == ''
    assert dt.topLevelItem(1).data(0, Qt.DisplayRole) == 'failure'
    assert dt.topLevelItem(1).data(1, Qt.DisplayRole) == 'test_fail'
    assert dt.topLevelItem(1).data(1, Qt.ToolTipRole) == 'test_foo.test_fail'


def test_run_tests_using_unittest_and_display_results(qtbot, tmpdir,
                                                      monkeypatch):
    """Basic check."""
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath

    with open(testfilename, 'w') as f:
        f.write("import unittest\n"
                "class MyTest(unittest.TestCase):\n"
                "   def test_ok(self): self.assertEqual(1+1, 2)\n"
                "   def test_fail(self): self.assertEqual(1+1, 3)\n")

    MockQMessageBox = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.unittestgui.QMessageBox',
                        MockQMessageBox)

    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=tmpdir.strpath, framework='unittest')
    with qtbot.waitSignal(widget.sig_finished, timeout=10000, raising=True):
        widget.run_tests(config)

    MockQMessageBox.assert_not_called()
    dt = widget.datatree
    assert dt.topLevelItemCount() == 2
    assert dt.topLevelItem(0).data(0, Qt.DisplayRole) == 'FAIL'
    assert dt.topLevelItem(0).data(1, Qt.DisplayRole) == 'test_fail'
    assert (dt.topLevelItem(0).data(1, Qt.ToolTipRole) ==
            'test_foo.MyTest.test_fail')
    assert dt.topLevelItem(0).data(2, Qt.DisplayRole) == ''
    assert dt.topLevelItem(1).data(0, Qt.DisplayRole) == 'ok'
    assert dt.topLevelItem(1).data(1, Qt.DisplayRole) == 'test_ok'
    assert (dt.topLevelItem(1).data(1, Qt.ToolTipRole) ==
            'test_foo.MyTest.test_ok')
    assert dt.topLevelItem(1).data(2, Qt.DisplayRole) == ''
