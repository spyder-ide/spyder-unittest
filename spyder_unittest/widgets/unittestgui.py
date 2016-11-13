# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Spyder Project Developers
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Unit Testing widget."""

from __future__ import with_statement

# Standard library imports
import os
import os.path as osp
import sys
import time

# Third party imports
from lxml import etree
from qtpy.compat import getexistingdirectory
from qtpy.QtCore import (QByteArray, QProcess, QProcessEnvironment, Qt,
                         QTextCodec, Signal)
from qtpy.QtGui import QBrush, QColor, QFont
from qtpy.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMessageBox,
                            QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from spyder.config.base import get_conf_path, get_translation
from spyder.py3compat import getcwd, to_text_string
from spyder.utils import icon_manager as ima
from spyder.utils.misc import add_pathlist_to_PYTHONPATH
from spyder.utils.qthelpers import create_toolbutton
from spyder.widgets.comboboxes import PathComboBox
from spyder.widgets.variableexplorer.texteditor import TextEditor

# Local imports
from spyder_unittest.widgets.configdialog import Config, ask_for_config

locale_codec = QTextCodec.codecForLocale()

# This is needed for testing this module as a stand alone script
try:
    _ = get_translation("unittest", dirname="spyder_unittest")
except KeyError as error:
    import gettext
    _ = gettext.gettext

COL_POS = 0  # Position is not displayed but set as Qt.UserRole

COLOR_OK = QBrush(QColor("#C1FFBA"))
COLOR_SKIP = QBrush(QColor("#C5C5C5"))
COLOR_FAIL = QBrush(QColor("#FF0000"))
COLORS = {
    "ok": COLOR_OK,
    "failure": COLOR_FAIL,  # py.test
    "error": COLOR_FAIL,  # nose
    "skipped": COLOR_SKIP,  # py.test, nose
}


def is_unittesting_installed():
    """Check if the program and the library for line_profiler is installed."""
    # return (programs.is_module_installed('line_profiler')
    # and programs.find_program('kernprof.py') is not None)
    return True


class UnitTestWidget(QWidget):
    """
    Unit testing widget.

    Fields
    ------
    config : Config
        Configuration for running tests.

    Signals
    -------
    sig_finished: Emitted when plugin finishes processing tests.
    """

    DATAPATH = get_conf_path('unittest.results')
    VERSION = '0.0.1'

    sig_finished = Signal()

    def __init__(self, parent):
        """Unit testing widget."""
        QWidget.__init__(self, parent)

        self.setWindowTitle("Unit testing")

        self.output = None
        self.error_output = None

        self.config = Config()
        self._last_pythonpath = None

        self.config_button = create_toolbutton(
            self,
            icon=ima.icon('configure'),
            text=_('Config'),
            tip=_('Configure tests'),
            triggered=self.configure,
            text_beside_icon=True)
        self.start_button = create_toolbutton(
            self,
            icon=ima.icon('run'),
            text=_("Run tests"),
            tip=_("Run unit testing"),
            triggered=self.start_test_process,
            text_beside_icon=True)
        self.stop_button = create_toolbutton(
            self,
            icon=ima.icon('stop'),
            text=_("Stop"),
            tip=_("Stop current profiling"),
            text_beside_icon=True)

        self.datelabel = QLabel()

        self.log_button = create_toolbutton(
            self,
            icon=ima.icon('log'),
            text=_("Output"),
            text_beside_icon=True,
            tip=_("Show program's output"),
            triggered=self.show_log)

        self.datatree = UnitTestDataTree(self)

        self.collapse_button = create_toolbutton(
            self,
            icon=ima.icon('collapse'),
            triggered=lambda dD=-1: self.datatree.collapseAll(),
            tip=_('Collapse all'))
        self.expand_button = create_toolbutton(
            self,
            icon=ima.icon('expand'),
            triggered=lambda dD=1: self.datatree.expandAll(),
            tip=_('Expand all'))

        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(self.config_button)
        hlayout1.addWidget(self.start_button)
        hlayout1.addWidget(self.stop_button)

        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(self.collapse_button)
        hlayout2.addWidget(self.expand_button)
        hlayout2.addStretch()
        hlayout2.addWidget(self.datelabel)
        hlayout2.addStretch()
        hlayout2.addWidget(self.log_button)

        layout = QVBoxLayout()
        layout.addLayout(hlayout1)
        layout.addLayout(hlayout2)
        layout.addWidget(self.datatree)
        self.setLayout(layout)

        self.process = None
        self.set_running_state(False)

        if not is_unittesting_installed():
            for widget in (self.datatree, self.log_button, self.start_button,
                           self.stop_button, self.collapse_button,
                           self.expand_button):
                widget.setDisabled(True)
            text = _('<b>Please install the unittesting module</b>')
            self.datelabel.setText(text)
            self.datelabel.setOpenExternalLinks(True)
        else:
            pass  # self.show_data()

    def analyze(self, wdir, pythonpath=None, framework=None):
        """Run tests."""
        if not is_unittesting_installed():
            return
        self.kill_if_running()
        self.start_test_process(wdir, pythonpath, framework)

    def show_log(self):
        """Show output of testing process."""
        if self.output:
            TextEditor(
                self.output,
                title=_("Unit testing output"),
                readonly=True,
                size=(700, 500)).exec_()

    def show_errorlog(self):
        """Show errors of testing process."""
        if self.error_output:
            TextEditor(
                self.error_output,
                title=_("Unit testing output"),
                readonly=True,
                size=(700, 500)).exec_()

    def configure(self):
        """Configure tests."""
        oldconfig = self.config
        config = ask_for_config(oldconfig)
        if config:
            self.config = config

    def start_test_process(self, wdir=None, pythonpath=None, framework=None):
        """
        Start the process for running tests.

        First ask user to configure test process.
        The process's output is consumed by `read_output()`.
        When the process finishes, the `finish` signal is emitted.

        Parameters
        ----------
        wdir : str
            working directory to switch to when running tests.
        pythonpath : list of str
            directories to be added to system python path.
            If None, use `self._last_pythonpath`.
        framework : str or None
            test framework; can be 'nose' or 'py.test' or None
        """
        oldconfig = Config(framework or self.config.framework, wdir or
                           self.config.wdir)
        config = ask_for_config(oldconfig)
        if config is None:  # if user pressed Cancel
            return
        framework = config.framework
        wdir = config.wdir

        if pythonpath is None:
            pythonpath = self._last_pythonpath
        self._last_pythonpath = pythonpath

        self.datelabel.setText(_('Running tests, please wait...'))

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.SeparateChannels)
        self.process.setWorkingDirectory(wdir)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(
            lambda: self.read_output(error=True))
        self.process.finished.connect(self.finished)
        self.stop_button.clicked.connect(self.process.kill)

        if pythonpath is not None:
            env = [
                to_text_string(_pth)
                for _pth in self.process.systemEnvironment()
            ]
            add_pathlist_to_PYTHONPATH(env, pythonpath)
            processEnvironment = QProcessEnvironment()
            for envItem in env:
                envName, separator, envValue = envItem.partition('=')
                processEnvironment.insert(envName, envValue)
            self.process.setProcessEnvironment(processEnvironment)

        self.output = ''
        self.error_output = ''

        if framework == 'nose':
            executable = "nosetests"
            p_args = ['--with-xunit', "--xunit-file=%s" % self.DATAPATH]
        elif framework == 'py.test':
            executable = "py.test"
            p_args = ['--junit-xml', self.DATAPATH]
        else:
            raise ValueError('Unknown framework')

        if os.name == 'nt':
            executable += '.exe'

        self.process.start(executable, p_args)

        running = self.process.waitForStarted()
        self.set_running_state(running)

        if not running:
            QMessageBox.critical(self,
                                 _("Error"), _("Process failed to start"))

    def set_running_state(self, state=True):
        """Set running state."""
        self.start_button.setEnabled(not state)
        self.stop_button.setEnabled(state)

    def read_output(self, error=False):
        """Read output of testing process."""
        if error:
            self.process.setReadChannel(QProcess.StandardError)
        else:
            self.process.setReadChannel(QProcess.StandardOutput)
        qba = QByteArray()
        while self.process.bytesAvailable():
            if error:
                qba += self.process.readAllStandardError()
            else:
                qba += self.process.readAllStandardOutput()
        text = to_text_string(locale_codec.toUnicode(qba.data()))
        if error:
            self.error_output += text
        else:
            self.output += text

    def finished(self):
        """Testing has finished."""
        self.set_running_state(False)
        # self.show_errorlog()  # If errors occurred, show them.
        self.output = self.error_output + self.output
        self.show_data(justanalyzed=True)
        self.sig_finished.emit()

    def kill_if_running(self):
        """Kill testing process if it is running."""
        if self.process is not None:
            if self.process.state() == QProcess.Running:
                self.process.kill()
                self.process.waitForFinished()

    def show_data(self, justanalyzed=False):
        """Show test results."""
        if not justanalyzed:
            self.output = None
        self.log_button.setEnabled(
            self.output is not None and len(self.output) > 0)
        self.kill_if_running()

        self.datatree.load_data(self.DATAPATH)
        self.datelabel.setText(_('Sorting data, please wait...'))
        QApplication.processEvents()
        self.datatree.show_tree()

        text_style = "<span style=\'color: #444444\'><b>%s </b></span>"
        date_text = text_style % time.strftime("%d %b %Y %H:%M",
                                               time.localtime())
        self.datelabel.setText(date_text)


class UnitTestDataTree(QTreeWidget):
    """Convenience tree widget to store and view unit testing data."""

    def __init__(self, parent=None):
        """Convenience tree widget to store and view unit testing data."""
        QTreeWidget.__init__(self, parent)
        self.header_list = [
            _('Status'), _('Name'), _('Message'), _('Time (ms)')
        ]
        self.data = None  # To be filled by self.load_data()
        self.max_time = 0  # To be filled by self.load_data()
        self.header().setDefaultAlignment(Qt.AlignCenter)
        self.setColumnCount(len(self.header_list))
        self.setHeaderLabels(self.header_list)
        self.clear()
        self.setItemsExpandable(True)
        self.setSortingEnabled(False)
        # self.connect(self, SIGNAL('itemActivated(QTreeWidgetItem*,int)'),
        #              self.item_activated)

    def show_tree(self):
        """Populate the tree with unit testing data and display it."""
        self.clear()  # Clear before re-populating
        self.populate_tree()
        for col in range(self.columnCount() - 1):
            self.resizeColumnToContents(col)

    def load_data(self, profdatafile):
        """Load unit testing data."""
        self.data = etree.parse(profdatafile).getroot()

    def populate_tree(self):
        """Create each item (and associated data) in the tree."""
        if not len(self.data):
            warn_item = QTreeWidgetItem(self)
            warn_item.setData(0, Qt.DisplayRole, "No results to show.")
            warn_item.setFirstColumnSpanned(True)
            warn_item.setTextAlignment(0, Qt.AlignCenter)
            font = warn_item.font(0)
            font.setStyle(QFont.StyleItalic)
            warn_item.setFont(0, font)
            return

        try:
            monospace_font = self.window().editor.get_plugin_font()
        except AttributeError:  # If run standalone for testing
            monospace_font = QFont("Courier New")
            monospace_font.setPointSize(10)

        for testcase in self.data:
            testcase_item = QTreeWidgetItem(self)
            testcase_item.setData(1, Qt.DisplayRole, "{0}.{1}".format(
                testcase.get("classname"), testcase.get("name")))
            testcase_item.setData(3, Qt.DisplayRole,
                                  float(testcase.get("time")) * 1e3)

            if len(testcase):
                test_error = testcase[0]

                status = test_error.tag
                testcase_item.setData(0, Qt.DisplayRole, status)
                color = COLORS[status]
                for col in range(self.columnCount()):
                    testcase_item.setBackground(col, color)

                type_ = test_error.get("type")
                message = test_error.get("message")
                if type_ and message:
                    text = "{0}: {1}".format(type_, message)
                elif type_:
                    text = type_
                else:
                    text = message
                testcase_item.setData(2, Qt.DisplayRole, text)

                text = test_error.text
                if text:
                    for line in text.rstrip().split("\n"):
                        error_content_item = QTreeWidgetItem(testcase_item)
                        error_content_item.setData(0, Qt.DisplayRole, line)
                        error_content_item.setFirstColumnSpanned(True)
                        error_content_item.setFont(0, monospace_font)
            else:
                testcase_item.setData(0, Qt.DisplayRole, "ok")

    def item_activated(self, item):
        """Called if user clicks on item."""
        filename, line_no = item.data(COL_POS, Qt.UserRole)
        self.parent().edit_goto.emit(filename, line_no, '')


def test():
    """Run widget test."""
    from spyder.utils.qthelpers import qapplication
    app = qapplication()
    widget = UnitTestWidget(None)
    wdir = osp.normpath(osp.join(osp.dirname(__file__), osp.pardir))
    widget.config = Config('py.test', wdir)
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test()
