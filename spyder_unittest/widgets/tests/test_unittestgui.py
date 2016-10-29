# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Spyder Project Developers
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Tests for unittestgui.py."""

# Standard library imports
import os

# Third party imports
from pytestqt import qtbot
from qtpy.QtCore import Qt
import pytest

# Local imports
from spyder_unittest.widgets.unittestgui import UnitTestWidget

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


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
    with qtbot.waitSignal(widget.sig_finished, timeout=10000, raising=True):
        widget.analyze(tmpdir.strpath, framework=framework)

    MockQMessageBox.assert_not_called()
    dt = widget.datatree
    itemcount = dt.topLevelItemCount()
    assert itemcount == 2
    assert dt.topLevelItem(0).data(0, Qt.DisplayRole) == 'ok'
    assert dt.topLevelItem(0).data(1, Qt.DisplayRole) == 'test_foo.test_ok'
    assert dt.topLevelItem(0).data(2, Qt.DisplayRole) is None
    assert dt.topLevelItem(1).data(0, Qt.DisplayRole) == 'failure'
    assert dt.topLevelItem(1).data(1, Qt.DisplayRole) == 'test_foo.test_fail'
    if framework == 'py.test':
        expected = 'assert (1 + 1) == 3'
    else:
        expected = 'builtins.AssertionError'
    assert dt.topLevelItem(1).data(2, Qt.DisplayRole) == expected
