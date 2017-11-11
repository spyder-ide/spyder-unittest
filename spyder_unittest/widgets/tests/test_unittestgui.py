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
from spyder_unittest.widgets.configdialog import Config
from spyder_unittest.widgets.unittestgui import UnitTestWidget

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


def test_unittestgui_set_config_emits_newconfig(qtbot):
    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=os.getcwd(), framework='unittest')
    with qtbot.waitSignal(widget.sig_newconfig) as blocker:
        widget.config = config
    assert blocker.args == [config]
    assert widget.config == config


def test_unittestgui_set_config_does_not_emit_when_invalid(qtbot):
    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=os.getcwd(), framework=None)
    with qtbot.assertNotEmitted(widget.sig_newconfig):
        widget.config = config
    assert widget.config == config


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
    model = widget.datatree.model()
    assert model.rowCount() == 2
    assert model.index(0, 0).data(Qt.DisplayRole) == 'ok'
    assert model.index(0, 1).data(Qt.DisplayRole) == 'test_ok'
    assert model.index(0, 1).data(Qt.ToolTipRole) == 'test_foo.test_ok'
    assert model.index(0, 2).data(Qt.DisplayRole) == ''
    assert model.index(1, 0).data(Qt.DisplayRole) == 'failure'
    assert model.index(1, 1).data(Qt.DisplayRole) == 'test_fail'
    assert model.index(1, 1).data(Qt.ToolTipRole) == 'test_foo.test_fail'


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
    model = widget.datatree.model()
    assert model.rowCount() == 2
    assert model.index(0, 0).data(Qt.DisplayRole) == 'FAIL'
    assert model.index(0, 1).data(Qt.DisplayRole) == 'test_fail'
    assert model.index(0, 1).data(Qt.ToolTipRole) == 'test_foo.MyTest.test_fail'
    assert model.index(0, 2).data(Qt.DisplayRole) == ''
    assert model.index(1, 0).data(Qt.DisplayRole) == 'ok'
    assert model.index(1, 1).data(Qt.DisplayRole) == 'test_ok'
    assert model.index(1, 1).data(Qt.ToolTipRole) == 'test_foo.MyTest.test_ok'
    assert model.index(1, 2).data(Qt.DisplayRole) == ''
