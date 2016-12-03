# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Spyder Project Developers
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Classes for running tests within various frameworks."""

# Standard library imports
import os

# Third party imports
from qtpy.QtCore import (QByteArray, QObject, QProcess, QProcessEnvironment,
                         QTextCodec)
from qtpy.QtWidgets import QApplication
from spyder.config.base import get_conf_path
from spyder.py3compat import to_text_string
from spyder.utils.misc import add_pathlist_to_PYTHONPATH


class TestRunner(QObject):
    """Class for running tests with py.test or nose."""

    DATAPATH = get_conf_path('unittest.results')

    def __init__(self, widget, datatree):
        QObject.__init__(self, widget)
        self.widget = widget
        self.datatree = datatree
        self.output = None
        self.error_output = None
        self.process = None

    def start(self, config, pythonpath):
        """Raises RuntimeError if process failed to start."""

        framework = config.framework
        wdir = config.wdir

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.SeparateChannels)
        self.process.setWorkingDirectory(wdir)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(
            lambda: self.read_output(error=True))
        self.process.finished.connect(self.finished)

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
        if not running:
            raise RuntimeError

        self.datatree.clear()

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
        locale_codec = QTextCodec.codecForLocale()
        text = to_text_string(locale_codec.toUnicode(qba.data()))
        if error:
            self.error_output += text
        else:
            self.output += text

    def finished(self):
        """Testing has finished."""
        self.widget.set_running_state(False)
        self.output = self.error_output + self.output
        self.show_data(justanalyzed=True)
        self.widget.sig_finished.emit()

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
        self.widget.log_action.setEnabled(
            self.output is not None and len(self.output) > 0)
        self.kill_if_running()

        self.datatree.load_data(self.DATAPATH)
        QApplication.processEvents()
        msg = self.datatree.show_tree()
        self.widget.status_label.setText(msg)
