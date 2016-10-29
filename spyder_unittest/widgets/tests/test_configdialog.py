# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Spyder Project Developers
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------

"""Tests for configdialog.py."""

# Third party imports
from qtpy.QtWidgets import QDialogButtonBox

# Local imports
from spyder_unittest.widgets.configdialog import ConfigDialog

def test_configdialog_click_pytest(qtbot):
    configdialog = ConfigDialog()
    qtbot.addWidget(configdialog)
    configdialog.pytest_button.click()
    assert configdialog.config() == 'py.test'

def test_configdialog_ok_initially_disabled(qtbot):
    configdialog = ConfigDialog()
    qtbot.addWidget(configdialog)
    assert not configdialog.buttons.button(QDialogButtonBox.Ok).isEnabled()

def test_configdialog_clicking_pytest_enables_ok(qtbot):
    configdialog = ConfigDialog()
    qtbot.addWidget(configdialog)
    configdialog.pytest_button.click()
    assert configdialog.buttons.button(QDialogButtonBox.Ok).isEnabled()
