# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Unit Testing widget."""

from __future__ import with_statement

# Standard library imports
import os.path as osp
import sys

# Third party imports
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (QHBoxLayout, QLabel, QMenu, QMessageBox,
                            QToolButton, QVBoxLayout, QWidget)
from spyder.config.base import get_conf_path, get_translation
from spyder.utils import icon_manager as ima
from spyder.utils.qthelpers import create_action, create_toolbutton
from spyder.widgets.variableexplorer.texteditor import TextEditor

# Local imports
from spyder_unittest.backend.frameworkregistry import FrameworkRegistry
from spyder_unittest.backend.noserunner import NoseRunner
from spyder_unittest.backend.pytestrunner import PyTestRunner
from spyder_unittest.backend.unittestrunner import UnittestRunner
from spyder_unittest.widgets.configdialog import Config, ask_for_config
from spyder_unittest.widgets.datatree import DataTree

# This is needed for testing this module as a stand alone script
try:
    _ = get_translation("unittest", dirname="spyder_unittest")
except KeyError as error:
    import gettext
    _ = gettext.gettext

# Supported testing framework
FRAMEWORKS = {NoseRunner, PyTestRunner, UnittestRunner}


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
    config : Config or None
        Configuration for running tests, or `None` if not set.
    default_wdir : str
        Default choice of working directory.
    framework_registry : FrameworkRegistry
        Registry of supported testing frameworks.
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
    """

    VERSION = '0.0.1'

    sig_finished = Signal()
    sig_newconfig = Signal(Config)

    def __init__(self, parent, options_button=None, options_menu=None):
        """Unit testing widget."""
        QWidget.__init__(self, parent)

        self.setWindowTitle("Unit testing")

        self.config = None
        self.pythonpath = None
        self.default_wdir = None
        self.testrunner = None
        self.output = None
        self.datatree = DataTree(self)

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
        layout.addWidget(self.datatree)
        self.setLayout(layout)

        if not is_unittesting_installed():
            for widget in (self.datatree, self.log_action, self.start_button,
                           self.collapse_action, self.expand_action):
                widget.setDisabled(True)
        else:
            pass  # self.show_data()

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
            triggered=self.datatree.collapseAll())
        self.expand_action = create_action(
            self,
            text=_('Expand all'),
            icon=ima.icon('expand'),
            triggered=self.datatree.expandAll())
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
        return (config and config.framework and osp.isdir(config.wdir))

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
        self.testdetails = []
        tempfilename = get_conf_path('unittest.results')
        self.testrunner = self.framework_registry.create_runner(
            config.framework, self, tempfilename)
        self.testrunner.sig_finished.connect(self.process_finished)
        self.testrunner.sig_collected.connect(self.tests_collected)

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

    def tests_collected(self, testdetails):
        """
        Called when tests are collected.

        This function stores the tests and displays the total number of tests
        that have been collected.
        """
        self.testdetails += testdetails
        self.status_label.setText(
            _('Collected {} tests').format(len(self.testdetails)))


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
