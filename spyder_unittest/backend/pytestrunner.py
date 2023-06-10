# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for pytest framework."""

from __future__ import annotations

# Standard library imports
import os
import os.path as osp
import re
from typing import Any, Optional, TYPE_CHECKING

# Local imports
from spyder.config.base import get_translation
from spyder_unittest.backend.runnerbase import (Category, RunnerBase,
                                                TestResult, COV_TEST_NAME)
from spyder_unittest.backend.zmqreader import ZmqStreamReader
if TYPE_CHECKING:
    from spyder_unittest.widgets.configdialog import Config

try:
    _ = get_translation('spyder_unittest')
except KeyError:
    import gettext
    _ = gettext.gettext


class PyTestRunner(RunnerBase):
    """Class for running tests within pytest framework."""

    module = 'pytest'
    name = 'pytest'

    def create_argument_list(self, config: Config,
                             cov_path: Optional[str],
                             single_test: Optional[str]) -> list[str]:
        """Create argument list for testing process."""
        dirname = os.path.dirname(__file__)
        pyfile = os.path.join(dirname, 'workers', 'pytestworker.py')
        arguments = [pyfile, str(self.reader.port)]
        if config.coverage:
            arguments += [f'--cov={cov_path}', '--cov-report=term-missing']
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

    def process_output(self, output: list[dict[str, Any]]) -> None:
        """
        Process output of test process.

        Parameters
        ----------
        output
            list of decoded Python object sent by test process.
        """
        collected_list = []
        collecterror_list = []
        starttest_list = []
        result_list = []
        for result_item in output:
            if result_item['event'] == 'config':
                self.rootdir = result_item['rootdir']
            elif result_item['event'] == 'collected':
                name = self.convert_nodeid_to_testname(result_item['nodeid'])
                collected_list.append(name)
            elif result_item['event'] == 'collecterror':
                tupl = self.logreport_collecterror_to_tuple(result_item)
                collecterror_list.append(tupl)
            elif result_item['event'] == 'starttest':
                name = self.logreport_starttest_to_str(result_item)
                starttest_list.append(name)
            elif result_item['event'] == 'logreport':
                testresult = self.logreport_to_testresult(result_item)
                result_list.append(testresult)

        if collected_list:
            self.sig_collected.emit(collected_list)
        if collecterror_list:
            self.sig_collecterror.emit(collecterror_list)
        if starttest_list:
            self.sig_starttest.emit(starttest_list)
        if result_list:
            self.sig_testresult.emit(result_list)

    def process_coverage(self, output: str) -> None:
        """Search the output text for coverage details.

        Called by the function 'finished' at the very end.
        """
        cov_results = re.search(
            r'-*? coverage:.*?-*\nTOTAL\s.*?\s(\d*?)\%.*\n=*',
            output, flags=re.S)
        if cov_results:
            total_coverage = cov_results.group(1)
            cov_report = TestResult(
                Category.COVERAGE, f'{total_coverage}%', COV_TEST_NAME)
            # create a fake test, then emit the coverage as the result
            # This gives overall test coverage, used in TestDataModel.summary
            self.sig_collected.emit([COV_TEST_NAME])
            self.sig_testresult.emit([cov_report])

            # also build a result for each file's coverage
            header = "".join(cov_results.group(0).split("\n")[1:3])
            # coverage report columns:
            # Name  Stmts   Miss  Cover   Missing
            for row in re.findall(
                    r'^((.*?\.py) .*?(\d+%).*?(\d[\d\,\-\ ]*)?)$',
                    cov_results.group(0), flags=re.M):
                lineno: Optional[int] = None
                if row[3]:
                    match = re.search(r'^(\d*)', row[3])
                    if match:
                        lineno = int(match.group(1)) - 1
                file_cov = TestResult(
                    Category.COVERAGE, row[2], row[1],
                    message=_('Missing: {}').format(row[3] if row[3] else _("(none)")),
                    extra_text=_('{}\n{}').format(header, row[0]), filename=row[1],
                    lineno=lineno)
                self.sig_collected.emit([row[1]])
                self.sig_testresult.emit([file_cov])

    def finished(self, exitcode: int) -> None:
        """
        Called when the unit test process has finished.

        This function emits `sig_finished`.

        Parameters
        ----------
        exitcode
            Exit code of the test process.
        """
        self.reader.close()
        output = self.read_all_process_output()
        if self.config.coverage:
            self.process_coverage(output)
        normal_exit = exitcode in [0, 1, 2, 5]
        # Meaning of exit codes: 0 = all tests passed, 1 = test failed,
        # 2 = interrupted, 5 = no tests collected
        self.sig_finished.emit([], output, normal_exit)

    def normalize_module_name(self, name: str) -> str:
        """
        Convert module name reported by pytest to Python conventions.

        This function strips the .py suffix and replaces '/' by '.', so that
        'ham/spam.py' becomes 'ham.spam'.

        The result is relative to the directory from which tests are run and
        not the pytest root dir.
        """
        wdir = osp.realpath(self.config.wdir)
        if wdir != self.rootdir:
            abspath = osp.join(self.rootdir, name)
            try:
                name = osp.relpath(abspath, start=wdir)
            except ValueError:
                # Happens on Windows if paths are on different drives
                pass

        if name.endswith('.py'):
            name = name[:-3]
        return name.replace('/', '.')

    def convert_nodeid_to_testname(self, nodeid: str) -> str:
        """Convert a nodeid to a test name."""
        module, name = nodeid.split('::', 1)
        module = self.normalize_module_name(module)
        return '{}.{}'.format(module, name)

    def logreport_collecterror_to_tuple(
            self, report: dict[str, Any]) -> tuple[str, str]:
        """Convert a 'collecterror' logreport to a (str, str) tuple."""
        module = self.normalize_module_name(report['nodeid'])
        return (module, report['longrepr'])

    def logreport_starttest_to_str(self, report: dict[str, Any]) -> str:
        """Convert a 'starttest' logreport to a str."""
        return self.convert_nodeid_to_testname(report['nodeid'])

    def logreport_to_testresult(self, report: dict[str, Any]) -> TestResult:
        """Convert a logreport sent by test process to a TestResult."""
        status = report['outcome']
        if report['outcome'] in ('failed', 'xpassed') or report['witherror']:
            cat = Category.FAIL
        elif report['outcome'] in ('passed', 'xfailed'):
            cat = Category.OK
        else:
            cat = Category.SKIP
        testname = self.convert_nodeid_to_testname(report['nodeid'])
        message = report.get('message', '')
        extra_text = report.get('longrepr', '')
        if 'sections' in report:
            if extra_text:
                extra_text +=  '\n'
            for (heading, text) in report['sections']:
                extra_text += '----- {} -----\n{}'.format(heading, text)
        filename = osp.join(self.rootdir, report['filename'])
        result = TestResult(cat, status, testname, message=message,
                            time=report['duration'], extra_text=extra_text,
                            filename=filename, lineno=report['lineno'])
        return result
