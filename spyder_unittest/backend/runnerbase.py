# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Classes for running tests within various frameworks."""

# Standard library imports
from collections import namedtuple
import os
import tempfile

# Third party imports
from lxml import etree
from qtpy.QtCore import (QObject, QProcess, QProcessEnvironment, QTextCodec,
                         Signal)
from spyder.config.base import get_translation
from spyder.py3compat import to_text_string
from spyder.utils.misc import add_pathlist_to_PYTHONPATH, get_python_executable

try:
    from importlib.util import find_spec as find_spec_or_loader
except ImportError:  # Python 2
    from pkgutil import find_loader as find_spec_or_loader

try:
    _ = get_translation("unittest", dirname="spyder_unittest")
except KeyError as error:
    import gettext
    _ = gettext.gettext

# Class representing test results
TestResult = namedtuple('TestResult', [
    'category', 'status', 'name', 'module', 'message', 'time', 'extra_text'
])


class Category:
    """Enum type representing category of test result."""

    OK = 1
    FAIL = 2
    SKIP = 3


class RunnerBase(QObject):
    """
    Base class for running tests with a framework that uses JUnit XML.

    This is an abstract class, meant to be subclassed before being used.
    Concrete subclasses should define executable and create_argument_list(),

    All communication back to the caller is done via signals.

    Attributes
    ----------
    module : str
        Name of Python module for test framework. This needs to be defined
        before the user can run tests.
    name : str
        Name of test framework, as presented to user.
    process : QProcess or None
        Process running the unit test suite.
    resultfilename : str
        Name of file in which test results are stored.

    Signals
    -------
    sig_finished(list of TestResult, str)
        Emitted when test process finishes. First argument contains the test
        results, second argument contains the output of the test process.
    """

    sig_finished = Signal(object, str)

    def __init__(self, widget, resultfilename=None):
        """
        Construct test runner.

        Parameters
        ----------
        widget : UnitTestWidget
            Unit test widget which constructs the test runner.
        resultfilename : str or None
            Name of file in which to store test results. If None, use default.
        """
        QObject.__init__(self, widget)
        self.process = None
        if resultfilename is None:
            self.resultfilename = os.path.join(tempfile.gettempdir(),
                                               'unittest.results')
        else:
            self.resultfilename = resultfilename

    @classmethod
    def is_installed(cls):
        """
        Check whether test framework is installed.

        This function tests whether self.module is installed, but it does not
        import it.

        Returns
        -------
        bool
            True if framework is installed, False otherwise.
        """
        return find_spec_or_loader(cls.module) is not None

    def create_argument_list(self):
        """
        Create argument list for testing process (dummy).

        This function should be defined before calling self.start().
        """
        raise NotImplementedError

    def start(self, config, pythonpath):
        """
        Start process which will run the unit test suite.

        The process is run in the working directory specified in 'config',
        with the directories in `pythonpath` added to the Python path for the
        test process. The test results are written to the file
        `self.resultfilename`. The standard output and error are also recorded.
        Once the process is finished, `self.finished()` will be called.

        Parameters
        ----------
        config : TestConfig
            Unit test configuration.
        pythonpath : list of str
            List of directories to be added to the Python path

        Raises
        ------
        RuntimeError
            If process failed to start.
        """
        wdir = config.wdir

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.setWorkingDirectory(wdir)
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

        executable = get_python_executable()
        p_args = ['-m', self.module] + self.create_argument_list()

        try:
            os.remove(self.resultfilename)
        except OSError:
            pass

        self.process.start(executable, p_args)
        running = self.process.waitForStarted()
        if not running:
            raise RuntimeError

    def finished(self):
        """
        Called when the unit test process has finished.

        This function reads the results and emits `sig_finished`.
        """
        qbytearray = self.process.readAllStandardOutput()
        locale_codec = QTextCodec.codecForLocale()
        output = to_text_string(locale_codec.toUnicode(qbytearray.data()))
        testresults = self.load_data()
        self.sig_finished.emit(testresults, output)

    def kill_if_running(self):
        """Kill testing process if it is running."""
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()

    def load_data(self):
        """
        Read and parse unit test results.

        This function reads the unit test results from the file with name
        `self.resultfilename` and parses them. The file should contain the
        test results in JUnitXML format.

        Returns
        -------
        list of TestResult
            Unit test results.
        """
        try:
            data = etree.parse(self.resultfilename).getroot()
        except OSError:
            data = []

        testresults = []
        for testcase in data:
            category = Category.OK
            status = 'ok'
            module = testcase.get('classname')
            name = testcase.get('name')
            message = ''
            time = float(testcase.get('time'))
            extras = []

            for child in testcase:
                if child.tag in ('error', 'failure', 'skipped'):
                    if child.tag == 'skipped':
                        category = Category.SKIP
                    else:
                        category = Category.FAIL
                    status = child.tag
                    type_ = child.get('type')
                    message = child.get('message', default='')
                    if type_ and message:
                        message = '{0}: {1}'.format(type_, message)
                    elif type_:
                        message = type_
                    if child.text:
                        extras.append(child.text)
                elif child.tag in ('system-out', 'system-err'):
                    if child.tag == 'system-out':
                        heading = _('Captured stdout')
                    else:
                        heading = _('Captured stderr')
                    contents = child.text.rstrip('\n')
                    extras.append('----- {} -----\n{}'.format(heading,
                                                              contents))

            extra_text = '\n\n'.join(extras)
            testresults.append(
                TestResult(category, status, name, module, message, time,
                           extra_text))

        return testresults
