# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for configdialog.py."""

# Standard library imports
import os

# Third party imports
from qtpy.QtWidgets import QDialogButtonBox

# Local imports
from spyder_unittest.widgets.configdialog import Config, ConfigDialog

frameworks = ['nose', 'py.test']


def default_config():
    return Config(framework=None, wdir=os.getcwd())


def test_configdialog_uses_frameworks(qtbot):
    frameworks = ['spam', 'ham', 'eggs']
    configdialog = ConfigDialog(frameworks, default_config())
    assert configdialog.framework_combobox.count() == len(frameworks)
    for i in range(len(frameworks)):
        assert configdialog.framework_combobox.itemText(i) == frameworks[i]


def test_configdialog_sets_initial_config(qtbot):
    config = default_config()
    configdialog = ConfigDialog(frameworks, config)
    assert configdialog.get_config() == config


def test_configdialog_click_pytest(qtbot):
    configdialog = ConfigDialog(frameworks, default_config())
    qtbot.addWidget(configdialog)
    configdialog.framework_combobox.setCurrentIndex(1)
    assert configdialog.get_config().framework == 'py.test'


def test_configdialog_ok_initially_disabled(qtbot):
    configdialog = ConfigDialog(frameworks, default_config())
    qtbot.addWidget(configdialog)
    assert not configdialog.buttons.button(QDialogButtonBox.Ok).isEnabled()


def test_configdialog_ok_setting_framework_initially_enables_ok(qtbot):
    config = Config(framework='py.test', wdir=os.getcwd())
    configdialog = ConfigDialog(frameworks, config)
    qtbot.addWidget(configdialog)
    assert configdialog.buttons.button(QDialogButtonBox.Ok).isEnabled()


def test_configdialog_clicking_pytest_enables_ok(qtbot):
    configdialog = ConfigDialog(frameworks, default_config())
    qtbot.addWidget(configdialog)
    configdialog.framework_combobox.setCurrentIndex(1)
    assert configdialog.buttons.button(QDialogButtonBox.Ok).isEnabled()


def test_configdialog_wdir_lineedit(qtbot):
    configdialog = ConfigDialog(frameworks, default_config())
    qtbot.addWidget(configdialog)
    wdir = os.path.normpath(os.path.join(os.getcwd(), os.path.pardir))
    configdialog.wdir_lineedit.setText(wdir)
    assert configdialog.get_config().wdir == wdir


def test_configdialog_wdir_button(qtbot, monkeypatch):
    configdialog = ConfigDialog(frameworks, default_config())
    qtbot.addWidget(configdialog)
    wdir = os.path.normpath(os.path.join(os.getcwd(), os.path.pardir))
    monkeypatch.setattr(
        'spyder_unittest.widgets.configdialog.getexistingdirectory',
        lambda parent, caption, basedir: wdir)
    configdialog.wdir_button.click()
    assert configdialog.get_config().wdir == wdir
