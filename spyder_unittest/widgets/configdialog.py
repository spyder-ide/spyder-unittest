# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Spyder Project Developers
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------

# Third party imports
from qtpy.QtWidgets import (QApplication, QDialog, QDialogButtonBox,
                            QRadioButton, QVBoxLayout)


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
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
        if self.pytest_button.isChecked():
            return 'py.test'
        elif self.nose_button.isChecked():
            return 'nose'


def get_config(parent=None):
    dialog = ConfigDialog(parent)
    result = dialog.exec_()
    if result == QDialog.Accepted:
        return dialog.config()


if __name__ == '__main__':
    app = QApplication([])
    print(get_config())
