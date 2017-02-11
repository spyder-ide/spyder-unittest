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
from qtpy.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QGroupBox,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QRadioButton, QVBoxLayout)
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

    The window contains two radio buttons (for 'py,test' and 'nose'),
    a line edit box for specifying the working directory, a button to
    use a file browser for selecting the directory, and OK and Cancel
    buttons. Initially, neither radio button is selected and the OK
    button is disabled. Selecting a radio button enabled the OK
    button.
    """

    def __init__(self, config, parent=None):
        """
        Construct a dialog window.

        Parameters
        ----------
        config : Config
            Initial configuration
        parent : QWidget
        """
        super(ConfigDialog, self).__init__(parent)
        self.setWindowTitle(_('Configure tests'))
        layout = QVBoxLayout(self)

        framework_groupbox = QGroupBox(_('Test framework'), self)
        framework_layout = QVBoxLayout(framework_groupbox)
        self.pytest_button = QRadioButton('py.test', framework_groupbox)
        framework_layout.addWidget(self.pytest_button)
        self.nose_button = QRadioButton('nose', framework_groupbox)
        framework_layout.addWidget(self.nose_button)
        layout.addWidget(framework_groupbox)

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

        ok_button = self.buttons.button(QDialogButtonBox.Ok)
        ok_button.setEnabled(False)
        self.pytest_button.toggled.connect(lambda: ok_button.setEnabled(True))
        self.nose_button.toggled.connect(lambda: ok_button.setEnabled(True))

        if config.framework == 'py.test':
            self.pytest_button.setChecked(True)
        elif config.framework == 'nose':
            self.nose_button.setChecked(True)
        self.wdir_lineedit.setText(config.wdir)

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
        if self.pytest_button.isChecked():
            framework = 'py.test'
        elif self.nose_button.isChecked():
            framework = 'nose'
        else:
            framework = None
        return Config(framework=framework, wdir=self.wdir_lineedit.text())


def ask_for_config(config, parent=None):
    """
    Ask user to specify a test configuration.

    This is a convenience function which displays a modal dialog window
    of type `ConfigDialog`.
    """
    dialog = ConfigDialog(config, parent)
    result = dialog.exec_()
    if result == QDialog.Accepted:
        return dialog.get_config()


if __name__ == '__main__':
    app = QApplication([])
    config = Config(framework=None, wdir=getcwd())
    print(ask_for_config(config))
