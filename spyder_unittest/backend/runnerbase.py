# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Classes for running tests within various frameworks."""

from __future__ import annotations

# Standard library imports
from enum import IntEnum
import os
import tempfile
from typing import ClassVar, Optional, TYPE_CHECKING

# Third party imports
from qtpy.QtCore import (
    QObject, QProcess, QProcessEnvironment, QTextCodec, Signal)

# Local imports
if TYPE_CHECKING:
    from spyder_unittest.widgets.configdialog import Config
    from spyder_unittest.widgets.unittestgui import UnitTestWidget


# if generating coverage report, use this name for the TestResult
# it's here in case we can get coverage results from unittest too
COV_TEST_NAME = 'Total Test Coverage'


class Category(IntEnum):
    """Enum type representing category of test result."""

    FAIL = 1
    OK = 2
    SKIP = 3
    PENDING = 4
    COVERAGE = 5


class TestResult:
    """Class representing the result of running a single test."""

    __test__ = False  # this is not a pytest test class

    def __init__(self, category: Category, status: str, name: str,
                 message: str = '', time: Optional[float] = None,
                 extra_text: str = '', filename: Optional[str] = None,
                 lineno: Optional[int] = None):
        """
        Construct a test result.
        """
        self.category = category
        self.status = status
        self.name = name
        self.message = message
        self.time = time
        extra_text = extra_text.rstrip()
        if extra_text:
            self.extra_text = extra_text.split("\n")
        else:
            self.extra_text = []
        self.filename = filename
        self.lineno = lineno

    def __eq__(self, other: object) -> bool:
        """Test for equality."""
        if not isinstance(other, TestResult):
            return NotImplemented
        return self.__dict__ == other.__dict__


class RunnerBase(QObject):
    """
    Base class for running tests with a framework that uses JUnit XML.

    This is an abstract class, meant to be subclassed before being used.
    Concrete subclasses should define create_argument_list() and finished().

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
    sig_collected(list of str)
        Emitted when tests are collected.
    sig_collecterror(list of (str, str) tuples)
        Emitted when errors are encountered during collection. First element
        of tuple is test name, second element is error message.
    sig_starttest(list of str)
        Emitted just before tests are run.
    sig_testresult(list of TestResult)
        Emitted when tests are finished.
    sig_finished(list of TestResult, str, bool)
        Emitted when test process finishes. First argument contains the test
        results, second argument contains the output of the test process,
        third argument is True on normal exit, False on abnormal exit.
    sig_stop()
        Emitted when test process is being stopped.
    """

    module: ClassVar[str]
    name: ClassVar[str]

    sig_collected = Signal(object)
    sig_collecterror = Signal(object)
    sig_starttest = Signal(object)
    sig_testresult = Signal(object)
    sig_finished = Signal(object, str, bool)
    sig_stop = Signal()

    def __init__(self, widget: UnitTestWidget,
                 resultfilename: Optional[str] = None):
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
        self.process: Optional[QProcess] = None
        if resultfilename is None:
            self.resultfilename = os.path.join(tempfile.gettempdir(),
                                               'unittest.results')
        else:
            self.resultfilename = resultfilename

    def create_argument_list(self, config: Config,
                             cov_path: Optional[str],
                             single_test: Optional[str]) -> list[str]:
        """
        Create argument list for testing process (dummy).

        This function should be defined before calling self.start().
        """
        raise NotImplementedError

    def _prepare_process(self, config: Config,
                         pythonpath: list[str]) -> QProcess:
        """
        Prepare and return process for running the unit test suite.

        This sets the working directory and environment.
        """
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.setWorkingDirectory(config.wdir)
        process.finished.connect(self.finished)
        if pythonpath:
            env = QProcessEnvironment.systemEnvironment()
            old_python_path = env.value('PYTHONPATH', '')
            python_path_str = os.pathsep.join(pythonpath)
            if old_python_path:
                python_path_str += os.pathsep + old_python_path
            env.insert('PYTHONPATH', python_path_str)
            process.setProcessEnvironment(env)
        return process

    def start(self, config: Config, cov_path: Optional[str],
              executable: str, pythonpath: list[str],
              single_test: Optional[str]) -> None:
        """
        Start process which will run the unit test suite.

        The process is run in the working directory specified in 'config',
        with the directories in `pythonpath` added to the Python path for the
        test process. The test results are written to the file
        `self.resultfilename`. The standard output and error are also recorded.
        Once the process is finished, `self.finished()` will be called.

        Parameters
        ----------
        config
            Unit test configuration.
        cov_path
            Path to filter source for coverage report
        executable
            Path to Python executable
        pythonpath
            List of directories to be added to the Python path
        single_test
            If None, run all tests; otherwise, it is the name of the only test
            to be run.

        Raises
        ------
        RuntimeError
            If process failed to start.
        """
        self.process = self._prepare_process(config, pythonpath)
        p_args = self.create_argument_list(config, cov_path, single_test)
        try:
            os.remove(self.resultfilename)
        except OSError:
            pass
        self.process.start(executable, p_args)
        running = self.process.waitForStarted()
        if not running:
            raise RuntimeError

    def finished(self, exitcode: int) -> None:
        """
        Called when the unit test process has finished.

        This function should be implemented in derived classes. It should read
        the results (if necessary) and emit `sig_finished`.
        """
        raise NotImplementedError

    def read_all_process_output(self) -> str:
        """Read and return all output from `self.process` as unicode."""
        assert self.process is not None
        qbytearray = self.process.readAllStandardOutput()
        locale_codec = QTextCodec.codecForLocale()
        return locale_codec.toUnicode(qbytearray.data())

    def stop_if_running(self) -> None:
        """Stop testing process if it is running."""
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.sig_stop.emit()
