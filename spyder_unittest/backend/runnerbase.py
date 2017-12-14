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
from qtpy.QtCore import QObject, QProcess, QProcessEnvironment, Signal
from spyder.py3compat import to_text_string
from spyder.utils.misc import add_pathlist_to_PYTHONPATH, get_python_executable

try:
    from importlib.util import find_spec as find_spec_or_loader
except ImportError:  # Python 2
    from pkgutil import find_loader as find_spec_or_loader

# Class with details of the tests
TestDetails = namedtuple('TestDetails', ['name', 'module'])


class Category:
    """Enum type representing category of test result."""

    OK = 1
    FAIL = 2
    SKIP = 3
    PENDING = 4


class TestResult:
    """Class representing the result of running a single test."""

    def __init__(self, category, status, name, module, message='', time=None,
                 extra_text=''):
        """
        Construct a test result.

        Parameters
        ----------
        category : Category
        status : str
        name : str
        module : str
        message : str
        time : float or None
        extra_text : str
        """
        self.category = category
        self.status = status
        self.name = name
        self.module = module
        self.message = message
        self.time = time
        extra_text = extra_text.rstrip()
        if extra_text:
            self.extra_text = extra_text.split("\n")
        else:
            self.extra_text = []

    def __eq__(self, other):
        """Test for equality."""
        return self.__dict__ == other.__dict__


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
    sig_collected(list of TestDetails)
        Emitted when tests are collected.
    sig_starttest(list of TestDetails)
        Emitted just before tests are run.
    sig_testresult(list of TestResult)
        Emitted when tests are finished.
    sig_finished(list of TestResult, str)
        Emitted when test process finishes. First argument contains the test
        results, second argument contains the output of the test process.
    """

    sig_collected = Signal(object)
    sig_starttest = Signal(object)
    sig_testresult = Signal(object)
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

    def _prepare_process(self, config, pythonpath):
        """
        Prepare and return process for running the unit test suite.

        This sets the working directory and environment.
        """
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.setWorkingDirectory(config.wdir)
        process.finished.connect(self.finished)
        if pythonpath is not None:
            env = [
                to_text_string(_pth)
                for _pth in process.systemEnvironment()
            ]
            add_pathlist_to_PYTHONPATH(env, pythonpath)
            processEnvironment = QProcessEnvironment()
            for envItem in env:
                envName, separator, envValue = envItem.partition('=')
                processEnvironment.insert(envName, envValue)
            process.setProcessEnvironment(processEnvironment)
        return process

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
        self.process = self._prepare_process(config, pythonpath)
        executable = get_python_executable()
        p_args = self.create_argument_list()
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

        This function should be implemented in derived classes. It should read
        the results (if necessary) and emit `sig_finished`.
        """
        raise NotImplementedError

    def kill_if_running(self):
        """Kill testing process if it is running."""
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
