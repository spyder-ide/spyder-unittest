# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Functionality for asking the user to specify the test configuration.

The main entry point is `ask_for_config()`.
"""

from __future__ import annotations

# Standard library imports
from os import getcwd
import os.path as osp
import shlex
from typing import Optional, NamedTuple

# Third party imports
from qtpy.compat import getexistingdirectory
from qtpy.QtCore import Slot
from qtpy.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QCheckBox)
from spyder.config.base import get_translation
from spyder.utils import icon_manager as ima


try:
    _ = get_translation('spyder_unittest')
except KeyError:
    import gettext
    _ = gettext.gettext

class Config(NamedTuple):
    framework: Optional[str] = None
    wdir: str = ''
    coverage: bool = False
    args: list[str] = []


class ConfigDialog(QDialog):
    """
    Dialog window for specifying test configuration.

    The window contains a combobox with all the frameworks, a line edit box for
    specifying the working directory, a button to use a file browser for
    selecting the directory, and OK and Cancel buttons. Initially, no framework
    is selected and the OK button is disabled. Selecting a framework enables
    the OK button.
    """

    # Width of strut in the layout of the dialog window; this determines
    # the width of the dialog
    STRUT_WIDTH = 400

    # Extra vertical space added between elements in the dialog
    EXTRA_SPACE = 10

    def __init__(self, frameworks, config, versions, parent=None):
        """
        Construct a dialog window.

        Parameters
        ----------
        frameworks : dict of (str, type)
            Names of all supported frameworks with their associated class
            (assumed to be a subclass of RunnerBase)
        config : Config
            Initial configuration
        versions : dict
            Versions of testing frameworks and their plugins
        parent : QWidget
        """
        super().__init__(parent)
        self.versions = versions
        self.setWindowTitle(_('Configure tests'))
        layout = QVBoxLayout(self)
        layout.addStrut(self.STRUT_WIDTH)

        grid_layout = QGridLayout()

        # Combo box for selecting the test framework

        framework_label = QLabel(_('Test framework:'))
        grid_layout.addWidget(framework_label, 0, 0)

        self.framework_combobox = QComboBox(self)
        for ix, (name, runner) in enumerate(sorted(frameworks.items())):
            installed = versions[name]['available']
            if installed:
                label = name
            else:
                label = '{} ({})'.format(name, _('not available'))
            self.framework_combobox.addItem(label)
            self.framework_combobox.model().item(ix).setEnabled(installed)
        grid_layout.addWidget(self.framework_combobox, 0, 1)

        # Line edit field for adding extra command-line arguments

        args_label = QLabel(_('Command-line arguments:'))
        grid_layout.addWidget(args_label, 1, 0)

        self.args_lineedit = QLineEdit(self)
        args_toolTip = _('Extra command-line arguments when running tests')
        self.args_lineedit.setToolTip(args_toolTip)
        grid_layout.addWidget(self.args_lineedit, 1, 1)

        layout.addLayout(grid_layout)
        spacing = grid_layout.verticalSpacing() + self.EXTRA_SPACE
        grid_layout.setVerticalSpacing(spacing)

        layout.addSpacing(self.EXTRA_SPACE)

        # Checkbox for enabling coverage report

        coverage_label = _('Include coverage report in output')
        coverage_toolTip = _('Works only for pytest, requires pytest-cov')
        coverage_layout = QHBoxLayout()
        self.coverage_checkbox = QCheckBox(coverage_label, self)
        self.coverage_checkbox.setToolTip(coverage_toolTip)
        self.coverage_checkbox.setEnabled(False)
        coverage_layout.addWidget(self.coverage_checkbox)
        layout.addLayout(coverage_layout)

        layout.addSpacing(self.EXTRA_SPACE)

        # Line edit field for selecting directory

        wdir_label = QLabel(_('Directory from which to run tests:'))
        layout.addWidget(wdir_label)
        wdir_layout = QHBoxLayout()
        self.wdir_lineedit = QLineEdit(self)
        wdir_layout.addWidget(self.wdir_lineedit)
        self.wdir_button = QPushButton(ima.icon('DirOpenIcon'), '', self)
        self.wdir_button.setToolTip(_("Select directory"))
        self.wdir_button.clicked.connect(lambda: self.select_directory())
        wdir_layout.addWidget(self.wdir_button)
        layout.addLayout(wdir_layout)

        layout.addSpacing(2 * self.EXTRA_SPACE)

        # OK and Cancel buttons at the bottom

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok |
                                        QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.ok_button = self.buttons.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        self.framework_combobox.currentIndexChanged.connect(
            self.framework_changed)

        # Set initial values to agree with the given config

        self.framework_combobox.setCurrentIndex(-1)
        if config.framework:
            index = self.framework_combobox.findText(config.framework)
            if index != -1:
                self.framework_combobox.setCurrentIndex(index)
        self.coverage_checkbox.setChecked(config.coverage)
        self.enable_coverage_checkbox_if_available()
        self.args_lineedit.setText(shlex.join(config.args))
        self.wdir_lineedit.setText(config.wdir)

    @Slot(int)
    def framework_changed(self, index):
        """Called when selected framework changes."""
        if index != -1:
            self.ok_button.setEnabled(True)
            self.enable_coverage_checkbox_if_available()

    def enable_coverage_checkbox_if_available(self):
        """
        Enable coverage checkbox only if coverage is available.

        Coverage is only implemented for pytest and requires pytest_cov.
        Enable the coverage checkbox if these conditions are satisfied,
        otherwise, disable and un-check the checkbox.
        """
        if (str(self.framework_combobox.currentText()) != 'pytest'
                or 'pytest-cov' not in self.versions['pytest']['plugins']):
            self.coverage_checkbox.setEnabled(False)
            self.coverage_checkbox.setChecked(False)
        else:
            self.coverage_checkbox.setEnabled(True)

    def select_directory(self):
        """Display dialog for user to select working directory."""
        basedir = self.wdir_lineedit.text()
        if not osp.isdir(basedir):
            basedir = getcwd()
        title = _("Select directory")
        directory = getexistingdirectory(self, title, basedir)
        if directory:
            self.wdir_lineedit.setText(directory)

    def get_config(self):
        """
        Return the test configuration specified by the user.

        Returns
        -------
        Config
            Test configuration
        """
        framework = self.framework_combobox.currentText()
        if framework == '':
            framework = None

        args = self.args_lineedit.text()
        args = shlex.split(args)

        return Config(framework=framework, wdir=self.wdir_lineedit.text(),
                      coverage=self.coverage_checkbox.isChecked(), args=args)


def ask_for_config(frameworks, config, versions, parent=None):
    """
    Ask user to specify a test configuration.

    This is a convenience function which displays a modal dialog window
    of type `ConfigDialog`.
    """
    dialog = ConfigDialog(frameworks, config, versions, parent)
    result = dialog.exec_()
    if result == QDialog.Accepted:
        return dialog.get_config()


if __name__ == '__main__':
    app = QApplication([])
    frameworks = {
        'nose2': object,
        'unittest': object,
        'pytest': object}
    versions = {
        'nose2': {'available': False},
        'unittest': {'available': True},
        'pytest': {'available': True, 'plugins': {'pytest-cov', '3.1.4'}}
    }
    config = Config(wdir=getcwd())
    print(ask_for_config(frameworks, config, versions))
