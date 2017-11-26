# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for py.test framework."""

# Standard library imports
import os

# Third party imports
from qtpy.QtCore import QProcess, QProcessEnvironment, QTextCodec
from spyder.py3compat import to_text_string
from spyder.utils.misc import add_pathlist_to_PYTHONPATH, get_python_executable

# Local imports
from spyder_unittest.backend.jsonstream import JSONStreamReader
from spyder_unittest.backend.runnerbase import (Category, RunnerBase,
                                                TestDetails, TestResult)


class PyTestRunner(RunnerBase):
    """Class for running tests within py.test framework."""

    module = 'pytest'
    name = 'py.test'

    def create_argument_list(self):
        """Create argument list for testing process."""
        pyfile = os.path.join(os.path.dirname(__file__), 'pytestworker.py')
        return [pyfile, '--junit-xml', self.resultfilename]

    def start(self, config, pythonpath):
        # TODO: Refactor to eliminate duplication with RunnerBase.start()
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
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)

        self.reader = JSONStreamReader()

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
        p_args = self.create_argument_list()

        try:
            os.remove(self.resultfilename)
        except OSError:
            pass

        self.process.start(executable, p_args)
        running = self.process.waitForStarted()
        if not running:
            raise RuntimeError

    def read_output(self):
        """Called when test process emits output."""
        qbytearray = self.process.readAllStandardOutput()
        locale_codec = QTextCodec.codecForLocale()
        output = to_text_string(locale_codec.toUnicode(qbytearray.data()))
        result = self.reader.consume(output)
        self.process_output(result)

    def process_output(self, output):
        """
        Process output of test process.

        Parameters
        ----------
        output : list
            list of decoded Python object sent by test process.
        """
        details_list = []
        result_list = []
        for result_item in output:
            if result_item['event'] == 'collected':
                details = TestDetails(result_item['name'],
                                      result_item['module'])
                details_list.append(details)
            elif result_item['event'] == 'logreport':
                result_list.append(self.logreport_to_testresult(result_item))
        if details_list:
            self.sig_collected.emit(details_list)
        if result_list:
            self.sig_testresult.emit(result_list)

    def logreport_to_testresult(self, report):
        """Convert a logreport sent by test process to a TestResult."""
        if report['outcome'] == 'passed':
            cat = Category.OK
            status = 'ok'
        elif report['outcome'] == 'failed':
            cat = Category.FAIL
            status = 'failure'
        else:
            cat = Category.SKIP
            status = report['outcome']
        module, name = report['nodeid'].split('::', maxsplit=1)
        duration = report['duration']
        message = report['message'] if 'message' in report else ''
        if 'longrepr' not in report:
            extra_text = ''
        elif isinstance(report['longrepr'], list):
            extra_text = report['longrepr'][2]
        else:
            extra_text = report['longrepr']
        if 'sections' in report:
            for (heading, text) in report['sections']:
                extra_text += '----- {} -----\n'.format(heading)
                extra_text += text
        result = TestResult(cat, status, name, module, message=message,
                            time=duration, extra_text=extra_text)
        return result
