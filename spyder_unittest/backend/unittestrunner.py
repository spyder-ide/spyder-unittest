# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for unittest framework."""

from __future__ import annotations

# Standard library imports
import os.path as osp
from typing import Any, Optional

# Local imports
from spyder_unittest.widgets.configdialog import Config
from spyder_unittest.backend.runnerbase import Category, RunnerBase, TestResult
from spyder_unittest.backend.zmqreader import ZmqStreamReader


class UnittestRunner(RunnerBase):
    """Class for running tests with unittest module in standard library."""

    module = 'unittest'
    name = 'unittest'

    def create_argument_list(self, config: Config,
                             cov_path: Optional[str],
                             single_test: Optional[str]) -> list[str]:
        """Create argument list for testing process."""
        dirname = osp.dirname(__file__)
        pyfile = osp.join(dirname, 'workers', 'unittestworker.py')
        arguments = [pyfile, str(self.reader.port)]
        arguments += config.args
        return arguments

    def start(self, config: Config, cov_path: Optional[str],
              executable: str, pythonpath: list[str],
              single_test: Optional[str]) -> None:
        """Start process which will run the unit test suite."""
        self.config = config
        self.reader = ZmqStreamReader()
        self.reader.sig_received.connect(self.process_output)
        super().start(config, cov_path, executable, pythonpath, single_test)

    def finished(self, exitcode: int) -> None:
        """
        Called when the unit test process has finished.

        This function reads the process output and emits `sig_finished`.
        """
        self.reader.close()
        output = self.read_all_process_output()
        self.sig_finished.emit([], output, True)

    def process_output(self, output: list[dict[str, Any]]) -> None:
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
                collected_list.append(result_item['id'])
            elif result_item['event'] == 'startTest':
                starttest_list.append(result_item['id'])
            elif result_item['event'].startswith('add'):
                testresult = add_event_to_testresult(result_item)
                result_list.append(testresult)

        if collected_list:
            self.sig_collected.emit(collected_list)
        if starttest_list:
            self.sig_starttest.emit(starttest_list)
        if result_list:
            self.sig_testresult.emit(result_list)


def add_event_to_testresult(event: dict[str, Any]) -> TestResult:
    """Convert an addXXX event sent by test process to a TestResult."""
    status = event['event'][3].lower() + event['event'][4:]
    if status in ('error', 'failure', 'unexpectedSuccess'):
        cat = Category.FAIL
    elif status in ('success', 'expectedFailure'):
        cat = Category.OK
    else:
        cat = Category.SKIP
    testname = event['id']
    message = event.get('reason', '')
    extra_text = event.get('err', '')
    result = TestResult(cat, status, testname, message=message,
                        extra_text=extra_text)
    return result
