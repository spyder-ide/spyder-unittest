# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Spyder Project Developers
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""
Functionality for asking the user to specify the test configuration.

The main entry point is `ask_for_config()`.
"""

# Third party imports
from qtpy.QtWidgets import (QApplication, QDialog, QDialogButtonBox,
                            QRadioButton, QVBoxLayout)


class ConfigDialog(QDialog):
    """
    Dialog window for specifying test configuration.

    The window contains two radio buttons (for 'py,test' and 'nose') and OK
    and Cancel buttons. Initially, neither radio button is selected and the OK
    button is disabled. Selecting a radio button enabled the OK button.
    """

    def __init__(self, parent=None):
        """
        Construct a dialog window.

        Parameters
        ----------
        parent : QWidget
        """
        super(ConfigDialog, self).__init__(parent)
        self.setWindowTitle('Configure tests')
        layout = QVBoxLayout(self)

        self.pytest_button = QRadioButton('py.test', self)
        layout.addWidget(self.pytest_button)
        self.nose_button = QRadioButton('nose', self)
        layout.addWidget(self.nose_button)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok |
                                        QDialogButtonBox.Cancel, self)
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        ok_button = self.buttons.button(QDialogButtonBox.Ok)
        ok_button.setEnabled(False)
        self.pytest_button.clicked.connect(lambda: ok_button.setEnabled(True))
        self.nose_button.clicked.connect(lambda: ok_button.setEnabled(True))

    def config(self):
        """
        Return the test configuration specified by the user.

        Returns
        -------
        str or None
            Test framework, or None if dialog window was cancelled
        """
        if self.pytest_button.isChecked():
            return 'py.test'
        elif self.nose_button.isChecked():
            return 'nose'


def ask_for_config(parent=None):
    """
    Ask user to specify a test configuration.

    This is a convenience function which displays a modal dialog window
    of type `ConfigDialog`.
    """
    dialog = ConfigDialog(parent)
    result = dialog.exec_()
    if result == QDialog.Accepted:
        return dialog.config()


if __name__ == '__main__':
    app = QApplication([])
    print(ask_for_config())
