# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Unit Testing widget."""

from __future__ import with_statement

# Standard library imports
import copy
import os.path as osp
import sys

# Third party imports
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (QHBoxLayout, QLabel, QMenu, QMessageBox,
                            QToolButton, QVBoxLayout, QWidget)
from spyder.config.base import get_conf_path, get_translation
from spyder.utils import icon_manager as ima
from spyder.utils.qthelpers import create_action, create_toolbutton
from spyder.plugins.variableexplorer.widgets.texteditor import TextEditor

# Local imports
from spyder_unittest.backend.frameworkregistry import FrameworkRegistry
from spyder_unittest.backend.noserunner import NoseRunner
from spyder_unittest.backend.pytestrunner import PyTestRunner
from spyder_unittest.backend.runnerbase import Category, TestResult
from spyder_unittest.backend.unittestrunner import UnittestRunner
from spyder_unittest.widgets.configdialog import Config, ask_for_config
from spyder_unittest.widgets.datatree import TestDataModel, TestDataView

# This is needed for testing this module as a stand alone script
try:
    _ = get_translation("unittest", dirname="spyder_unittest")
except KeyError:
    import gettext
    _ = gettext.gettext

# Supported testing framework
FRAMEWORKS = {NoseRunner, PyTestRunner, UnittestRunner}


class UnitTestWidget(QWidget):
    """
    Unit testing widget.

    Attributes
    ----------
    config : Config or None
        Configuration for running tests, or `None` if not set.
    default_wdir : str
        Default choice of working directory.
    framework_registry : FrameworkRegistry
        Registry of supported testing frameworks.
    pre_test_hook : function returning bool or None
        If set, contains function to run before running tests; abort the test
        run if hook returns False.
    pythonpath : list of str
        Directories to be added to the Python path when running tests.
    testrunner : TestRunner or None
        Object associated with the current test process, or `None` if no test
        process is running at the moment.

    Signals
    -------
    sig_finished: Emitted when plugin finishes processing tests.
    sig_newconfig(Config): Emitted when test config is changed.
        Argument is new config, which is always valid.
    sig_edit_goto(str, int): Emitted if editor should go to some position.
        Arguments are file name and line number (zero-based).
    """

    VERSION = '0.0.1'

    sig_finished = Signal()
    sig_newconfig = Signal(Config)
    sig_edit_goto = Signal(str, int)

    def __init__(self, parent, options_button=None, options_menu=None):
        """Unit testing widget."""
        QWidget.__init__(self, parent)

        self.setWindowTitle("Unit testing")

        self.config = None
        self.pythonpath = None
        self.default_wdir = None
        self.pre_test_hook = None
        self.testrunner = None

        self.output = None
        self.testdataview = TestDataView(self)
        self.testdatamodel = TestDataModel(self)
        self.testdataview.setModel(self.testdatamodel)
        self.testdataview.sig_edit_goto.connect(self.sig_edit_goto)
        self.testdatamodel.sig_summary.connect(self.set_status_label)

        self.framework_registry = FrameworkRegistry()
        for runner in FRAMEWORKS:
            self.framework_registry.register(runner)

        self.start_button = create_toolbutton(self, text_beside_icon=True)
        self.set_running_state(False)

        self.status_label = QLabel('', self)

        self.create_actions()

        self.options_menu = options_menu or QMenu()
        self.options_menu.addAction(self.config_action)
        self.options_menu.addAction(self.log_action)
        self.options_menu.addAction(self.collapse_action)
        self.options_menu.addAction(self.expand_action)

        self.options_button = options_button or QToolButton(self)
        self.options_button.setIcon(ima.icon('tooloptions'))
        self.options_button.setPopupMode(QToolButton.InstantPopup)
        self.options_button.setMenu(self.options_menu)
        self.options_button.setAutoRaise(True)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.start_button)
        hlayout.addStretch()
        hlayout.addWidget(self.status_label)
        hlayout.addStretch()
        hlayout.addWidget(self.options_button)

        layout = QVBoxLayout()
        layout.addLayout(hlayout)
        layout.addWidget(self.testdataview)
        self.setLayout(layout)

    @property
    def config(self):
        """Return current test configuration."""
        return self._config

    @config.setter
    def config(self, new_config):
        """Set test configuration and emit sig_newconfig if valid."""
        self._config = new_config
        if self.config_is_valid():
            self.sig_newconfig.emit(new_config)

    def set_config_without_emit(self, new_config):
        """Set test configuration but do not emit any signal."""
        self._config = new_config

    def use_dark_interface(self, flag):
        """Set whether widget should use colours appropriate for dark UI."""
        self.testdatamodel.is_dark_interface = flag

    def create_actions(self):
        """Create the actions for the unittest widget."""
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
            triggered=self.testdataview.collapseAll)
        self.expand_action = create_action(
            self,
            text=_('Expand all'),
            icon=ima.icon('expand'),
            triggered=self.testdataview.expandAll)
        return [
            self.config_action, self.log_action, self.collapse_action,
            self.expand_action
        ]

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
        frameworks = self.framework_registry.frameworks
        config = ask_for_config(frameworks, oldconfig)
        if config:
            self.config = config

    def config_is_valid(self, config=None):
        """
        Return whether configuration for running tests is valid.

        Parameters
        ----------
        config : Config or None
            configuration for unit tests. If None, use `self.config`.
        """
        if config is None:
            config = self.config
        return (config and config.framework
                and config.framework in self.framework_registry.frameworks
                and osp.isdir(config.wdir))

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

        First, run `self.pre_test_hook` if it is set, and abort if its return
        value is `False`.

        Then, run the unit tests.

        The process's output is consumed by `read_output()`.
        When the process finishes, the `finish` signal is emitted.

        Parameters
        ----------
        config : Config or None
            configuration for unit tests. If None, use `self.config`.
            In either case, configuration should be valid.
        """
        if self.pre_test_hook:
            if self.pre_test_hook() is False:
                return

        if config is None:
            config = self.config
        pythonpath = self.pythonpath
        self.testdatamodel.testresults = []
        self.testdetails = []
        tempfilename = get_conf_path('unittest.results')
        self.testrunner = self.framework_registry.create_runner(
            config.framework, self, tempfilename)
        self.testrunner.sig_finished.connect(self.process_finished)
        self.testrunner.sig_collected.connect(self.tests_collected)
        self.testrunner.sig_collecterror.connect(self.tests_collect_error)
        self.testrunner.sig_starttest.connect(self.tests_started)
        self.testrunner.sig_testresult.connect(self.tests_yield_result)

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
        Change start/stop button according to whether tests are running.

        If tests are running, then display a stop button, otherwise display
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
            button.setText(_('Stop'))
            button.setToolTip(_('Stop current test process'))
            if self.testrunner:
                button.clicked.connect(self.testrunner.stop_if_running)
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

        Parameters
        ----------
        testresults : list of TestResult or None
            `None` indicates all test results have already been transmitted.
        output : str
        """
        self.output = output
        self.set_running_state(False)
        self.testrunner = None
        self.log_action.setEnabled(bool(output))
        if testresults is not None:
            self.testdatamodel.testresults = testresults
        self.replace_pending_with_not_run()
        self.sig_finished.emit()

    def replace_pending_with_not_run(self):
        """Change status of pending tests to 'not run''."""
        new_results = []
        for res in self.testdatamodel.testresults:
            if res.category == Category.PENDING:
                new_res = copy.copy(res)
                new_res.category = Category.SKIP
                new_res.status = _('not run')
                new_results.append(new_res)
        if new_results:
            self.testdatamodel.update_testresults(new_results)

    def tests_collected(self, testnames):
        """Called when tests are collected."""
        testresults = [TestResult(Category.PENDING, _('pending'), name)
                       for name in testnames]
        self.testdatamodel.add_testresults(testresults)

    def tests_started(self, testnames):
        """Called when tests are about to be run."""
        testresults = [TestResult(Category.PENDING, _('pending'), name,
                                  message=_('running'))
                       for name in testnames]
        self.testdatamodel.update_testresults(testresults)

    def tests_collect_error(self, testnames_plus_msg):
        """Called when errors are encountered during collection."""
        testresults = [TestResult(Category.FAIL, _('failure'), name,
                                  message=_('collection error'),
                                  extra_text=msg)
                       for name, msg in testnames_plus_msg]
        self.testdatamodel.add_testresults(testresults)

    def tests_yield_result(self, testresults):
        """Called when test results are received."""
        self.testdatamodel.update_testresults(testresults)

    def set_status_label(self, msg):
        """
        Set status label to the specified message.

        Arguments
        ---------
        msg: str
        """
        self.status_label.setText('<b>{}</b>'.format(msg))


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
    widget.config = Config('pytest', wdir)

    # add wdir's parent to python path, so that `import spyder_unittest` works
    rootdir = osp.abspath(osp.join(wdir, osp.pardir))
    widget.pythonpath = rootdir

    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test()
