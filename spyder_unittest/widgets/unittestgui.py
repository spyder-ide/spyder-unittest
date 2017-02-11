# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Unit Testing widget."""

from __future__ import with_statement

# Standard library imports
from collections import Counter
import os.path as osp
import sys

# Third party imports
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QBrush, QColor, QFont
from qtpy.QtWidgets import (QHBoxLayout, QLabel, QMenu, QMessageBox,
                            QToolButton, QTreeWidget, QTreeWidgetItem,
                            QVBoxLayout, QWidget)
from spyder.config.base import get_conf_path, get_translation
from spyder.utils import icon_manager as ima
from spyder.utils.qthelpers import create_action, create_toolbutton
from spyder.widgets.variableexplorer.texteditor import TextEditor

# Local imports
from spyder_unittest.backend.testrunner import Category, TestRunner
from spyder_unittest.widgets.configdialog import Config, ask_for_config

# This is needed for testing this module as a stand alone script
try:
    _ = get_translation("unittest", dirname="spyder_unittest")
except KeyError as error:
    import gettext
    _ = gettext.gettext

COL_POS = 0  # Position is not displayed but set as Qt.UserRole

COLORS = {
    Category.OK: QBrush(QColor("#C1FFBA")),
    Category.FAIL: QBrush(QColor("#FF0000")),
    Category.SKIP: QBrush(QColor("#C5C5C5"))
}


def is_unittesting_installed():
    """Check if the program and the library for line_profiler is installed."""
    # return (programs.is_module_installed('line_profiler')
    # and programs.find_program('kernprof.py') is not None)
    return True


class UnitTestWidget(QWidget):
    """
    Unit testing widget.

    Attributes
    ----------
    config : Config
        Configuration for running tests.
    default_wdir : str
        Default choice of working directory.
    pythonpath : list of str
        Directories to be added to the Python path when running tests.
    testrunner : TestRunner or None
        Object associated with the current test process, or `None` if no test
        process is running at the moment.

    Signals
    -------
    sig_finished: Emitted when plugin finishes processing tests.
    """

    VERSION = '0.0.1'

    sig_finished = Signal()

    def __init__(self, parent):
        """Unit testing widget."""
        QWidget.__init__(self, parent)

        self.setWindowTitle("Unit testing")

        self.config = None
        self.pythonpath = None
        self.default_wdir = None
        self.testrunner = None
        self.output = None
        self.datatree = UnitTestDataTree(self)

        self.start_button = create_toolbutton(self, text_beside_icon=True)
        self.set_running_state(False)

        self.status_label = QLabel('', self)

        self.config_action = create_action(
            self,
            text=_("Configure ..."),
            icon=ima.icon('configure'),
            triggered=self.configure)
        self.log_action = create_action(
            self,
            text=_('Show output'),
            icon=ima.icon('log'),
            triggered=self.show_log)
        self.collapse_action = create_action(
            self,
            text=_('Collapse all'),
            icon=ima.icon('collapse'),
            triggered=self.datatree.collapseAll())
        self.expand_action = create_action(
            self,
            text=_('Expand all'),
            icon=ima.icon('expand'),
            triggered=self.datatree.expandAll())

        options_menu = QMenu()
        options_menu.addAction(self.config_action)
        options_menu.addAction(self.log_action)
        options_menu.addAction(self.collapse_action)
        options_menu.addAction(self.expand_action)

        self.options_button = QToolButton(self)
        self.options_button.setIcon(ima.icon('tooloptions'))
        self.options_button.setPopupMode(QToolButton.InstantPopup)
        self.options_button.setMenu(options_menu)
        self.options_button.setAutoRaise(True)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.start_button)
        hlayout.addStretch()
        hlayout.addWidget(self.status_label)
        hlayout.addStretch()
        hlayout.addWidget(self.options_button)

        layout = QVBoxLayout()
        layout.addLayout(hlayout)
        layout.addWidget(self.datatree)
        self.setLayout(layout)

        if not is_unittesting_installed():
            for widget in (self.datatree, self.log_action, self.start_button,
                           self.collapse_action, self.expand_action):
                widget.setDisabled(True)
        else:
            pass  # self.show_data()

    def show_log(self):
        """Show output of testing process."""
        if self.output:
            TextEditor(
                self.output,
                title=_("Unit testing output"),
                readonly=True,
                size=(700, 500)).exec_()

    def configure(self):
        """Configure tests."""
        if self.config:
            oldconfig = self.config
        else:
            oldconfig = Config(wdir=self.default_wdir)
        config = ask_for_config(oldconfig)
        if config:
            self.config = config

    def config_is_valid(self):
        """Return whether configuration for running tests is valid."""
        return (self.config and self.config.framework and
                osp.isdir(self.config.wdir))

    def maybe_configure_and_start(self):
        """
        Ask for configuration if necessary and then run tests.

        If the current test configuration is not valid (or not set(,
        then ask the user to configure. Then run the tests.
        """
        if not self.config_is_valid():
            self.configure()
        if self.config_is_valid():
            self.run_tests()

    def run_tests(self, config=None):
        """
        Run unit tests.

        The process's output is consumed by `read_output()`.
        When the process finishes, the `finish` signal is emitted.

        Parameters
        ----------
        config : Config or None
            configuration for unit tests. If None, use `self.config`.
            In either case, configuration should be valid.
        """
        if config is None:
            config = self.config
        pythonpath = self.pythonpath
        self.datatree.clear()
        tempfilename = get_conf_path('unittest.results')
        self.testrunner = TestRunner(self, tempfilename)
        self.testrunner.sig_finished.connect(self.process_finished)

        try:
            self.testrunner.start(config, pythonpath)
        except RuntimeError:
            QMessageBox.critical(self,
                                 _("Error"), _("Process failed to start"))
        else:
            self.set_running_state(True)
            self.status_label.setText(_('<b>Running tests ...<b>'))

    def set_running_state(self, state):
        """
        Change start/kill button according to whether tests are running.

        If tests are running, then display a kill button, otherwise display
        a start button.

        Parameters
        ----------
        state : bool
            Set to True if tests are running.
        """
        button = self.start_button
        try:
            button.clicked.disconnect()
        except TypeError:  # raised if not connected to any handler
            pass
        if state:
            button.setIcon(ima.icon('stop'))
            button.setText(_('Kill'))
            button.setToolTip(_('Kill current test process'))
            if self.testrunner:
                button.clicked.connect(self.testrunner.kill_if_running)
        else:
            button.setIcon(ima.icon('run'))
            button.setText(_("Run tests"))
            button.setToolTip(_('Run unit tests'))
            button.clicked.connect(
                lambda checked: self.maybe_configure_and_start())

    def process_finished(self, testresults, output):
        """
        Called when unit test process finished.

        This function collects and shows the test results and output.
        """
        self.output = output
        self.set_running_state(False)
        self.testrunner = None
        self.log_action.setEnabled(bool(output))
        self.datatree.testresults = testresults
        msg = self.datatree.show_tree()
        self.status_label.setText(msg)
        self.sig_finished.emit()


class UnitTestDataTree(QTreeWidget):
    """Convenience tree widget to store and view unit testing data."""

    def __init__(self, parent=None):
        """Convenience tree widget to store and view unit testing data."""
        QTreeWidget.__init__(self, parent)
        self.header_list = [
            _('Status'), _('Name'), _('Message'), _('Time (ms)')
        ]
        self.testresults = []
        self.header().setDefaultAlignment(Qt.AlignCenter)
        self.setColumnCount(len(self.header_list))
        self.setHeaderLabels(self.header_list)
        self.clear()
        self.setItemsExpandable(True)
        self.setSortingEnabled(False)

    def show_tree(self):
        """Populate the tree with unit testing data and display it."""
        self.clear()  # Clear before re-populating
        msg = self.populate_tree()
        for col in range(self.columnCount() - 1):
            self.resizeColumnToContents(col)
        return msg

    def populate_tree(self):
        """Create each item (and associated data) in the tree."""
        if not len(self.testresults):
            return _('No results to show.')

        try:
            monospace_font = self.window().editor.get_plugin_font()
        except AttributeError:  # If run standalone for testing
            monospace_font = QFont("Courier New")
            monospace_font.setPointSize(10)

        for testresult in self.testresults:
            testcase_item = QTreeWidgetItem(self)
            testcase_item.setData(0, Qt.DisplayRole, testresult.status)
            testcase_item.setData(1, Qt.DisplayRole, testresult.name)
            testcase_item.setData(2, Qt.DisplayRole, testresult.message)
            testcase_item.setData(3, Qt.DisplayRole, testresult.time * 1e3)
            color = COLORS[testresult.category]
            for col in range(self.columnCount()):
                testcase_item.setBackground(col, color)
            if testresult.extra_text:
                for line in testresult.extra_text.rstrip().split("\n"):
                    error_content_item = QTreeWidgetItem(testcase_item)
                    error_content_item.setData(0, Qt.DisplayRole, line)
                    error_content_item.setFirstColumnSpanned(True)
                    error_content_item.setFont(0, monospace_font)

        counts = Counter(res.category for res in self.testresults)
        if counts[Category.FAIL] == 1:
            test_or_tests = _('test')
        else:
            test_or_tests = _('tests')
        failed_txt = '{} {} failed'.format(counts[Category.FAIL],
                                           test_or_tests)
        passed_txt = '{} passed'.format(counts[Category.OK])
        other_txt = '{} other'.format(counts[Category.SKIP])
        msg = '<b>{}, {}, {}</b>'.format(failed_txt, passed_txt, other_txt)
        return msg

    def item_activated(self, item):
        """Called if user clicks on item."""
        filename, line_no = item.data(COL_POS, Qt.UserRole)
        self.parent().edit_goto.emit(filename, line_no, '')


def test():
    """
    Run widget test.

    Show the unittest widgets, configured so that our own tests are run when
    the user clicks "Run tests".
    """
    from spyder.utils.qthelpers import qapplication
    app = qapplication()
    widget = UnitTestWidget(None)

    # set wdir to .../spyder_unittest
    wdir = osp.abspath(osp.join(osp.dirname(__file__), osp.pardir))
    widget.config = Config('py.test', wdir)

    # add wdir's parent to python path, so that `import spyder_unittest` works
    rootdir = osp.abspath(osp.join(wdir, osp.pardir))
    widget.pythonpath = rootdir

    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test()
