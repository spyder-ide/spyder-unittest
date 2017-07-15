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
import os.path as osp

# Third party imports
from qtpy.compat import getexistingdirectory
from qtpy.QtCore import Slot
from qtpy.QtWidgets import (QApplication, QComboBox, QDialog, QDialogButtonBox,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QVBoxLayout)
from spyder.config.base import get_translation
from spyder.py3compat import getcwd, to_text_string
from spyder.utils import icon_manager as ima

try:
    _ = get_translation("unittest", dirname="spyder_unittest")
except KeyError as error:
    import gettext
    _ = gettext.gettext

Config = namedtuple('Config', ['framework', 'wdir'])
Config.__new__.__defaults__ = (None, '')


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
        super(ConfigDialog, self).__init__(parent)
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

    @Slot(int)
    def framework_changed(self, index):
        """Called when selected framework changes."""
        if index != -1:
            self.ok_button.setEnabled(True)

    def select_directory(self):
        """Display dialog for user to select working directory."""
        basedir = to_text_string(self.wdir_lineedit.text())
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
        return Config(framework=framework, wdir=self.wdir_lineedit.text())


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
    frameworks = ['nose', 'py.test', 'unittest']
    config = Config(framework=None, wdir=getcwd())
    print(ask_for_config(frameworks, config))
