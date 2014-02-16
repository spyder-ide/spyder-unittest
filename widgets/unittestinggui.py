# -*- coding: utf-8 -*-
#
# Copyright © 2011 Santiago Jaramillo
# based on pylintgui.py by Pierre Raybaut
#
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
Unit Testing widget
"""

from __future__ import with_statement

from spyderlib.qt.QtGui import (QHBoxLayout, QWidget, QMessageBox, QVBoxLayout,
                                QLabel, QTreeWidget, QTreeWidgetItem,
                                QApplication, QBrush, QColor, QFont)
from spyderlib.qt.QtCore import SIGNAL, QProcess, QByteArray, Qt, QTextCodec
locale_codec = QTextCodec.codecForLocale()
from spyderlib.qt.compat import getexistingdirectory

import sys
import os
import os.path as osp
import time
import cPickle
import linecache
import inspect
import hashlib
from lxml import etree

# Local imports
from spyderlib.utils.qthelpers import create_toolbutton, get_icon
from spyderlib.utils import programs
from spyderlib.baseconfig import get_conf_path, get_translation
from spyderlib.widgets.texteditor import TextEditor
from spyderlib.widgets.comboboxes import PythonModulesComboBox
from spyderlib.widgets.externalshell import baseshell
from spyderlib.py3compat import to_text_string, getcwd
_ = get_translation("p_unittesting", dirname="spyderplugins")


COL_NO = 0
COL_HITS = 1
COL_TIME = 2
COL_PERHIT = 3
COL_PERCENT = 4
COL_LINE = 5
COL_POS = 0  # Position is not displayed but set as Qt.UserRole

CODE_NOT_RUN_COLOR = QBrush(QColor.fromRgb(128, 128, 128, 200))


COLOR_OK = QBrush(QColor("#C1FFBA"))
COLOR_SKIP = QBrush(QColor("#C5C5C5"))
COLOR_FAIL = QBrush(QColor("#FF0000"))
COLORS = {
    "ok": COLOR_OK,
    "failure": COLOR_FAIL,  # py.test
    "error": COLOR_FAIL,  # nose
    "skipped": COLOR_SKIP,  # py.test, nose
    }

WEBSITE_URL = 'http://pythonhosted.org/line_profiler/'


def is_unittesting_installed():
    """Checks if the program and the library for line_profiler is installed
    """
    return (programs.is_module_installed('line_profiler')
            and programs.find_program('kernprof.py') is not None)


class UnitTestingWidget(QWidget):
    """
    Unit testing widget
    """
    DATAPATH = get_conf_path('unittesting.results')
    VERSION = '0.0.1'

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.setWindowTitle("Unit testing")

        self.output = None
        self.error_output = None

        self._last_wdir = None
        self._last_args = None
        self._last_pythonpath = None

        self.filecombo = PythonModulesComboBox(self)

        self.start_button = create_toolbutton(
            self, icon=get_icon('run.png'),
            text=_("Run tests"),
            tip=_("Run unit testing"),
            triggered=self.start, text_beside_icon=True)
        self.stop_button = create_toolbutton(
            self,
            icon=get_icon('terminate.png'),
            text=_("Stop"),
            tip=_("Stop current profiling"),
            text_beside_icon=True)
        self.connect(self.filecombo, SIGNAL('valid(bool)'),
                     self.start_button.setEnabled)
        #self.connect(self.filecombo, SIGNAL('valid(bool)'), self.show_data)
        # FIXME: The combobox emits this signal on almost any event
        #        triggering show_data() too early, too often.

        browse_button = create_toolbutton(
            self, icon=get_icon('fileopen.png'),
            tip=_('Select Python script'),
            triggered=self.select_file)

        self.datelabel = QLabel()

        self.log_button = create_toolbutton(
            self, icon=get_icon('log.png'),
            text=_("Output"),
            text_beside_icon=True,
            tip=_("Show program's output"),
            triggered=self.show_log)

        self.datatree = UnitTestingDataTree(self)

        self.collapse_button = create_toolbutton(
            self,
            icon=get_icon('collapse.png'),
            triggered=lambda dD=-1: self.datatree.collapseAll(),
            tip=_('Collapse all'))
        self.expand_button = create_toolbutton(
            self,
            icon=get_icon('expand.png'),
            triggered=lambda dD=1: self.datatree.expandAll(),
            tip=_('Expand all'))

        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(self.filecombo)
        hlayout1.addWidget(browse_button)
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
        self.start_button.setEnabled(False)

        if not is_unittesting_installed():
            for widget in (self.datatree, self.filecombo, self.log_button,
                           self.start_button, self.stop_button, browse_button,
                           self.collapse_button, self.expand_button):
                widget.setDisabled(True)
            text = _(
                '<b>Please install the <a href="%s">line_profiler module</a></b>'
                ) % WEBSITE_URL
            self.datelabel.setText(text)
            self.datelabel.setOpenExternalLinks(True)
        else:
            pass  # self.show_data()

    def analyze(self, filename, wdir=None, args=None, pythonpath=None):
        if not is_unittesting_installed():
            return
        self.kill_if_running()
        #index, _data = self.get_data(filename)
        index = None  # FIXME: storing data is not implemented yet
        if index is None:
            self.filecombo.addItem(filename)
            self.filecombo.setCurrentIndex(self.filecombo.count()-1)
        else:
            self.filecombo.setCurrentIndex(self.filecombo.findText(filename))
        self.filecombo.selected()
        if self.filecombo.is_valid():
            if wdir is None:
                wdir = osp.dirname(filename)
            self.start(wdir, args, pythonpath)

    def select_file(self):
        self.emit(SIGNAL('redirect_stdio(bool)'), False)
        filename = getexistingdirectory(
            self, _("Select directory"), getcwd())
        self.emit(SIGNAL('redirect_stdio(bool)'), False)
        if filename:
            self.analyze(filename)

    def show_log(self):
        if self.output:
            TextEditor(self.output, title=_("Unit testing output"),
                       readonly=True, size=(700, 500)).exec_()

    def show_errorlog(self):
        if self.error_output:
            TextEditor(self.error_output, title=_("Unit testing output"),
                       readonly=True, size=(700, 500)).exec_()

    def start(self, wdir=None, args=None, pythonpath=None):
        filename = to_text_string(self.filecombo.currentText())
        if wdir is None:
            wdir = self._last_wdir
            if wdir is None:
                wdir = osp.basename(filename)
        print(filename)
        if os.name == 'nt':
            # On Windows, one has to replace backslashes by slashes to avoid
            # confusion with escape characters (otherwise, for example, '\t'
            # will be interpreted as a tabulation):
            filename = osp.normpath(filename).replace(os.sep, '/')
        if args is None:
            args = self._last_args
            if args is None:
                args = []
        if pythonpath is None:
            pythonpath = self._last_pythonpath
        self._last_wdir = wdir
        self._last_args = args
        self._last_pythonpath = pythonpath

        self.datelabel.setText(_('Running tests, please wait...'))

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.SeparateChannels)
        self.process.setWorkingDirectory(filename)
        self.connect(self.process, SIGNAL("readyReadStandardOutput()"),
                     self.read_output)
        self.connect(self.process, SIGNAL("readyReadStandardError()"),
                     lambda: self.read_output(error=True))
        self.connect(self.process,
                     SIGNAL("finished(int,QProcess::ExitStatus)"),
                     self.finished)
        self.connect(self.stop_button, SIGNAL("clicked()"), self.process.kill)

        if pythonpath is not None:
            env = [to_text_string(_pth)
                   for _pth in self.process.systemEnvironment()]
            baseshell.add_pathlist_to_PYTHONPATH(env, pythonpath)
            self.process.setEnvironment(env)

        self.output = ''
        self.error_output = ''

#        executable = "py.test"
#        p_args = ['--junit-xml', self.DATAPATH]

        executable = "nosetests"
        p_args = ['--with-xunit', "--xunit-file=%s" % self.DATAPATH]

        if args:
            p_args.extend(programs.shell_split(args))
        self.process.start(executable, p_args)

        running = self.process.waitForStarted()
        self.set_running_state(running)
        if not running:
            QMessageBox.critical(self, _("Error"),
                                 _("Process failed to start"))

    def set_running_state(self, state=True):
        self.start_button.setEnabled(not state)
        self.stop_button.setEnabled(state)

    def read_output(self, error=False):
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
        self.set_running_state(False)
        #self.show_errorlog()  # If errors occurred, show them.
        self.output = self.error_output + self.output
        # FIXME: figure out if show_data should be called here or
        #        as a signal from the combobox
        self.show_data(justanalyzed=True)

    def kill_if_running(self):
        if self.process is not None:
            if self.process.state() == QProcess.Running:
                self.process.kill()
                self.process.waitForFinished()

    def show_data(self, justanalyzed=False):
        if not justanalyzed:
            self.output = None
        self.log_button.setEnabled(
            self.output is not None and len(self.output) > 0)
        self.kill_if_running()
        filename = to_text_string(self.filecombo.currentText())
        if not filename:
            return

        self.datatree.load_data(self.DATAPATH)
        self.datelabel.setText(_('Sorting data, please wait...'))
        QApplication.processEvents()
        self.datatree.show_tree()

        text_style = "<span style=\'color: #444444\'><b>%s </b></span>"
        date_text = text_style % time.strftime("%d %b %Y %H:%M",
                                               time.localtime())
        self.datelabel.setText(date_text)


class UnitTestingDataTree(QTreeWidget):
    """
    Convenience tree widget (with built-in model)
    to store and view unit testing data.
    """
    def __init__(self, parent=None):
        QTreeWidget.__init__(self, parent)
        self.header_list = [
            _('Status'), _('Name'), _('Message'), _('Time (ms)')]
        self.data = None      # To be filled by self.load_data()
        self.max_time = 0      # To be filled by self.load_data()
        self.header().setDefaultAlignment(Qt.AlignCenter)
        self.setColumnCount(len(self.header_list))
        self.setHeaderLabels(self.header_list)
        self.clear()
        self.setItemsExpandable(True)
        self.setSortingEnabled(False)
#        self.connect(self, SIGNAL('itemActivated(QTreeWidgetItem*,int)'),
#                     self.item_activated)

    def show_tree(self):
        """Populate the tree with unit testing data and display it."""
        self.clear()  # Clear before re-populating
        self.populate_tree()
        for col in range(self.columnCount()-1):
            self.resizeColumnToContents(col)

    def load_data(self, profdatafile):
        """Load unit testing data"""
        self.data = etree.parse(profdatafile).getroot()

    def populate_tree(self):
        """Create each item (and associated data) in the tree"""
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
            testcase_item.setData(
                1, Qt.DisplayRole, "{0}.{1}".format(
                    testcase.get("classname"), testcase.get("name")))
            testcase_item.setData(
                3, Qt.DisplayRole, float(testcase.get("time")) * 1e3)

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
                        error_content_item.setData(
                            0, Qt.DisplayRole, line)
                        error_content_item.setFirstColumnSpanned(True)
                        error_content_item.setFont(0, monospace_font)
            else:
                testcase_item.setData(0, Qt.DisplayRole, "ok")

    def item_activated(self, item):
        filename, line_no = item.data(COL_POS, Qt.UserRole)
        self.parent().emit(SIGNAL("edit_goto(QString,int,QString)"),
                           filename, line_no, '')


def test():
    """Run widget test"""
    from spyderlib.utils.qthelpers import qapplication
    app = qapplication()
    widget = UnitTestingWidget(None)
    widget.resize(800, 600)
    widget.show()
    widget.analyze(osp.normpath(osp.join(osp.dirname(__file__), osp.pardir)))
    sys.exit(app.exec_())

if __name__ == '__main__':
    test()
