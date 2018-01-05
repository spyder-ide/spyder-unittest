# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for py.test framework."""

# Standard library imports
import os

# Local imports
from spyder_unittest.backend.jsonstream import JSONStreamReader
from spyder_unittest.backend.runnerbase import Category, RunnerBase, TestResult


class PyTestRunner(RunnerBase):
    """Class for running tests within py.test framework."""

    module = 'pytest'
    name = 'py.test'

    def create_argument_list(self):
        """Create argument list for testing process."""
        pyfile = os.path.join(os.path.dirname(__file__), 'pytestworker.py')
        return [pyfile]

    def _prepare_process(self, config, pythonpath):
        """Prepare and return process for running the unit test suite."""
        process = RunnerBase._prepare_process(self, config, pythonpath)
        process.readyReadStandardOutput.connect(self.read_output)
        return process

    def start(self, config, pythonpath):
        """Start process which will run the unit test suite."""
        self.reader = JSONStreamReader()
        self.output = ''
        RunnerBase.start(self, config, pythonpath)

    def read_output(self):
        """Called when test process emits output."""
        output = self.read_all_process_output()
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
        collected_list = []
        starttest_list = []
        result_list = []

        for result_item in output:
            if result_item['event'] == 'collected':
                collected_list.append(
                        self.logreport_collected_to_str(result_item))
            elif result_item['event'] == 'starttest':
                starttest_list.append(
                        self.logreport_starttest_to_str(result_item))
            elif result_item['event'] == 'logreport':
                result_list.append(self.logreport_to_testresult(result_item))
            elif result_item['event'] == 'finished':
                self.output = result_item['stdout']

        if collected_list:
            self.sig_collected.emit(collected_list)
        if starttest_list:
            self.sig_starttest.emit(starttest_list)
        if result_list:
            self.sig_testresult.emit(result_list)

    def normalize_module_name(self, name):
        """
        Convert module name reported by pytest to Python conventions.

        This function strips the .py suffix and replaces '/' by '.', so that
        'ham/spam.py' becomes 'ham.spam'.
        """
        if name.endswith('.py'):
            name = name[:-3]
        return name.replace('/', '.')

    def logreport_collected_to_str(self, report):
        """Convert a 'collected' logreport to a str."""
        module = self.normalize_module_name(report['module'])
        return '{}.{}'.format(module, report['name'])

    def logreport_starttest_to_str(self, report):
        """Convert a 'starttest' logreport to a str."""
        module, name = report['nodeid'].split('::', 1)
        module = self.normalize_module_name(module)
        return '{}.{}'.format(module, name)

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
        module, name = report['nodeid'].split('::', 1)
        module = self.normalize_module_name(module)
        testname = '{}.{}'.format(module, name)
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
        result = TestResult(cat, status, testname, message=message,
                            time=duration, extra_text=extra_text)
        return result

    def finished(self):
        """
        Called when the unit test process has finished.

        This function emits `sig_finished`.
        """
        self.sig_finished.emit(None, self.output)
