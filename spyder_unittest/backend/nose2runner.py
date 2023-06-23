# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for Nose framework."""

from __future__ import annotations

# Standard library imports
from typing import Optional, TYPE_CHECKING

# Third party imports
from lxml import etree
from spyder.config.base import get_translation

# Local imports
from spyder_unittest.backend.runnerbase import Category, RunnerBase, TestResult
if TYPE_CHECKING:
    from spyder_unittest.widgets.configdialog import Config

try:
    _ = get_translation('spyder_unittest')
except KeyError:
    import gettext
    _ = gettext.gettext


class Nose2Runner(RunnerBase):
    """Class for running tests within Nose framework."""

    module = 'nose2'
    name = 'nose2'

    def create_argument_list(self, config: Config,
                             cov_path: Optional[str],
                             single_test: Optional[str]) -> list[str]:
        """Create argument list for testing process."""
        arguments = [
            '-m', self.module, '--plugin=nose2.plugins.junitxml',
            '--junit-xml', '--junit-xml-path={}'.format(self.resultfilename)
        ]
        if single_test:
            arguments.append(single_test)
        arguments += config.args
        return arguments

    def finished(self, exitcode: int) -> None:
        """Called when the unit test process has finished."""
        output = self.read_all_process_output()
        testresults = self.load_data()
        self.sig_finished.emit(testresults, output, True)

    def load_data(self) -> list[TestResult]:
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
            return []

        testresults = []
        for testcase in data:
            category = Category.OK
            status = 'ok'
            name = '{}.{}'.format(testcase.get('classname'),
                                  testcase.get('name'))
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
                elif child.tag in ('system-out', 'system-err') and child.text:
                    if child.tag == 'system-out':
                        heading = _('Captured stdout')
                    else:
                        heading = _('Captured stderr')
                    contents = child.text.rstrip('\n')
                    extras.append('----- {} -----\n{}'.format(heading,
                                                              contents))

            extra_text = '\n\n'.join(extras)
            testresults.append(
                TestResult(category, status, name, message, time, extra_text))

        return testresults
