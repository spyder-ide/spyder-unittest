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


class SpamRunner:
    name = 'spam'

    @classmethod
    def is_installed(cls):
        return False


class HamRunner:
    name = 'ham'

    @classmethod
    def is_installed(cls):
        return True


class FakePytestRunner:
    name = 'pytest'

    @classmethod
    def is_installed(cls):
        return True


frameworks = {r.name: r for r in [HamRunner, FakePytestRunner, SpamRunner]}

versions = {
    'spam': {'available': False},
    'ham': {'available': True},
    'pytest': {'available': True, 'plugins': {'pytest-cov', '3.1.4'}}
}


def default_config():
    return Config(framework=None, wdir=os.getcwd(), coverage=False)


def test_configdialog_uses_frameworks(qtbot):
    configdialog = ConfigDialog(
        {'ham': HamRunner}, default_config(), versions)
    assert configdialog.framework_combobox.count() == 1
    assert configdialog.framework_combobox.itemText(0) == 'ham'


def test_configdialog_indicates_unvailable_frameworks(qtbot):
    configdialog = ConfigDialog(
        {'spam': SpamRunner}, default_config(), versions)
    assert configdialog.framework_combobox.count() == 1
    assert configdialog.framework_combobox.itemText(
        0) == 'spam (not available)'


def test_configdialog_disables_unavailable_frameworks(qtbot):
    configdialog = ConfigDialog(frameworks, default_config(), versions)
    model = configdialog.framework_combobox.model()
    assert model.item(0).isEnabled()  # ham
    assert model.item(1).isEnabled()  # pytest
    assert not model.item(2).isEnabled()  # spam


def test_configdialog_sets_initial_config(qtbot):
    config = default_config()
    configdialog = ConfigDialog(frameworks, config, versions)
    assert configdialog.get_config() == config


def test_configdialog_click_ham(qtbot):
    configdialog = ConfigDialog(frameworks, default_config(), versions)
    qtbot.addWidget(configdialog)
    configdialog.framework_combobox.setCurrentIndex(1)
    assert configdialog.get_config().framework == 'pytest'


def test_configdialog_ok_initially_disabled(qtbot):
    configdialog = ConfigDialog(frameworks, default_config(), versions)
    qtbot.addWidget(configdialog)
    assert not configdialog.buttons.button(QDialogButtonBox.Ok).isEnabled()


def test_configdialog_ok_setting_framework_initially_enables_ok(qtbot):
    config = Config(framework='ham', wdir=os.getcwd())
    configdialog = ConfigDialog(frameworks, config, versions)
    qtbot.addWidget(configdialog)
    assert configdialog.buttons.button(QDialogButtonBox.Ok).isEnabled()


def test_configdialog_clicking_pytest_enables_ok(qtbot):
    configdialog = ConfigDialog(frameworks, default_config(), versions)
    qtbot.addWidget(configdialog)
    configdialog.framework_combobox.setCurrentIndex(1)
    assert configdialog.buttons.button(QDialogButtonBox.Ok).isEnabled()


def test_configdialog_coverage_checkbox(qtbot, monkeypatch):
    configdialog = ConfigDialog(frameworks, default_config(), versions)
    qtbot.addWidget(configdialog)
    configdialog.framework_combobox.setCurrentIndex(1)
    configdialog.coverage_checkbox.click()
    assert configdialog.get_config().coverage is True


def test_configdialog_coverage_checkbox_pytestcov_noinstall(qtbot, monkeypatch):
    local_versions = versions.copy()
    local_versions['pytest']['plugins'] = {}
    configdialog = ConfigDialog(frameworks, default_config(), local_versions)
    qtbot.addWidget(configdialog)
    configdialog.framework_combobox.setCurrentIndex(1)
    assert configdialog.coverage_checkbox.isEnabled() is False


def test_configdialog_wdir_lineedit(qtbot):
    configdialog = ConfigDialog(frameworks, default_config(), versions)
    qtbot.addWidget(configdialog)
    wdir = os.path.normpath(os.path.join(os.getcwd(), os.path.pardir))
    configdialog.wdir_lineedit.setText(wdir)
    assert configdialog.get_config().wdir == wdir


def test_configdialog_wdir_button(qtbot, monkeypatch):
    configdialog = ConfigDialog(frameworks, default_config(), versions)
    qtbot.addWidget(configdialog)
    wdir = os.path.normpath(os.path.join(os.getcwd(), os.path.pardir))
    monkeypatch.setattr(
        'spyder_unittest.widgets.configdialog.getexistingdirectory',
        lambda parent, caption, basedir: wdir)
    configdialog.wdir_button.click()
    assert configdialog.get_config().wdir == wdir
