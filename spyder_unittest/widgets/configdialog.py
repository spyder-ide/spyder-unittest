# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Functionality for asking the user to specify the test configuration.

The main entry point is `ask_for_config()`.
"""

# Standard library imports
from collections import namedtuple
from os import getcwd
import os.path as osp

# Third party imports
from qtpy.compat import getexistingdirectory
from qtpy.QtCore import Slot
from qtpy.QtWidgets import (QApplication, QComboBox, QDialog, QDialogButtonBox,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QVBoxLayout, QCheckBox)
from spyder.config.base import get_translation
from spyder.utils import icon_manager as ima

try:
    from importlib.util import find_spec as find_spec_or_loader
except ImportError:  # Python 2
    from pkgutil import find_loader as find_spec_or_loader

try:
    _ = get_translation('spyder_unittest')
except KeyError:
    import gettext
    _ = gettext.gettext

Config = namedtuple('Config', ['framework', 'wdir', 'coverage'])
Config.__new__.__defaults__ = (None, '', False)


class ConfigDialog(QDialog):
    """
    Dialog window for specifying test configuration.

    The window contains a combobox with all the frameworks, a line edit box for
    specifying the working directory, a button to use a file browser for
    selecting the directory, and OK and Cancel buttons. Initially, no framework
    is selected and the OK button is disabled. Selecting a framework enables
    the OK button.
    """

    def __init__(self, frameworks, config, parent=None):
        """
        Construct a dialog window.

        Parameters
        ----------
        frameworks : dict of (str, type)
            Names of all supported frameworks with their associated class
            (assumed to be a subclass of RunnerBase)
        config : Config
            Initial configuration
        parent : QWidget
        """
        super().__init__(parent)
        self.setWindowTitle(_('Configure tests'))
        layout = QVBoxLayout(self)

        framework_layout = QHBoxLayout()
        framework_label = QLabel(_('Test framework'))
        framework_layout.addWidget(framework_label)

        self.framework_combobox = QComboBox(self)
        for ix, (name, runner) in enumerate(sorted(frameworks.items())):
            installed = runner.is_installed()
            if installed:
                label = name
            else:
                label = '{} ({})'.format(name, _('not available'))
            self.framework_combobox.addItem(label)
            self.framework_combobox.model().item(ix).setEnabled(installed)

        framework_layout.addWidget(self.framework_combobox)
        layout.addLayout(framework_layout)

        layout.addSpacing(10)

        coverage_label = _('Include coverage report in output')
        coverage_toolTip = _('Works only for pytest, requires pytest-cov')
        coverage_layout = QHBoxLayout()
        self.coverage_checkbox = QCheckBox(coverage_label, self)
        self.coverage_checkbox.setToolTip(coverage_toolTip)
        self.coverage_checkbox.setEnabled(False)
        coverage_layout.addWidget(self.coverage_checkbox)
        layout.addLayout(coverage_layout)

        layout.addSpacing(10)

        wdir_label = QLabel(_('Directory from which to run tests'))
        layout.addWidget(wdir_label)
        wdir_layout = QHBoxLayout()
        self.wdir_lineedit = QLineEdit(self)
        wdir_layout.addWidget(self.wdir_lineedit)
        self.wdir_button = QPushButton(ima.icon('DirOpenIcon'), '', self)
        self.wdir_button.setToolTip(_("Select directory"))
        self.wdir_button.clicked.connect(lambda: self.select_directory())
        wdir_layout.addWidget(self.wdir_button)
        layout.addLayout(wdir_layout)

        layout.addSpacing(20)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok |
                                        QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.ok_button = self.buttons.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        self.framework_combobox.currentIndexChanged.connect(
            self.framework_changed)

        self.framework_combobox.setCurrentIndex(-1)
        if config.framework:
            index = self.framework_combobox.findText(config.framework)
            if index != -1:
                self.framework_combobox.setCurrentIndex(index)
        self.wdir_lineedit.setText(config.wdir)
        self.coverage_checkbox.setChecked(config.coverage)

    @Slot(int)
    def framework_changed(self, index):
        """Called when selected framework changes."""
        if index != -1:
            self.ok_button.setEnabled(True)
            # Coverage is only implemented for pytest, and requires pytest_cov
            if (str(self.framework_combobox.currentText()) in ['nose',
                                                              'unittest']
                    or find_spec_or_loader("pytest_cov") is None):
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
        return Config(framework=framework, wdir=self.wdir_lineedit.text(),
                      coverage=self.coverage_checkbox.isChecked())


def ask_for_config(frameworks, config, parent=None):
    """
    Ask user to specify a test configuration.

    This is a convenience function which displays a modal dialog window
    of type `ConfigDialog`.
    """
    dialog = ConfigDialog(frameworks, config, parent)
    result = dialog.exec_()
    if result == QDialog.Accepted:
        return dialog.get_config()


if __name__ == '__main__':
    app = QApplication([])
    frameworks = ['nose', 'pytest', 'unittest']
    config = Config(framework=None, wdir=getcwd(), coverage=False)
    print(ask_for_config(frameworks, config))
