# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for unittest framework."""

# Standard library imports
import re

# Local imports
from spyder_unittest.backend.runnerbase import Category, RunnerBase, TestResult


class UnittestRunner(RunnerBase):
    """Class for running tests with unittest module in standard library."""

    module = 'unittest'
    name = 'unittest'

    def create_argument_list(self):
        """Create argument list for testing process."""
        return ['-m', self.module, 'discover', '-v']

    def finished(self):
        """
        Called when the unit test process has finished.

        This function reads the results and emits `sig_finished`.
        """
        output = self.read_all_process_output()
        testresults = self.load_data(output)
        self.sig_finished.emit(testresults, output)

    def load_data(self, output):
        """
        Read and parse output from unittest module.

        Any parsing errors are silently ignored.

        Returns
        -------
        list of TestResult
            Unit test results.
        """
        res = []
        lines = output.splitlines()
        line_index = 0

        while lines[line_index]:
            data = self.try_parse_result(lines[line_index])
            if data:
                if data[2] == 'ok':
                    cat = Category.OK
                elif data[2] == 'FAIL' or data[2] == 'ERROR':
                    cat = Category.FAIL
                else:
                    cat = Category.SKIP
                name = '{}.{}'.format(data[1], data[0])
                tr = TestResult(category=cat, status=data[2], name=name,
                                message=data[3])
                res.append(tr)
            line_index += 1

        line_index += 1
        while not (lines[line_index]
                   and all(c == '-' for c in lines[line_index])):
            data = self.try_parse_exception_block(lines, line_index)
            if data:
                line_index = data[0]
                test_index = next(
                    i for i, tr in enumerate(res)
                    if tr.name == '{}.{}'.format(data[2], data[1]))
                res[test_index].extra_text = data[3]
            else:
                line_index += 1

        return res

    def try_parse_result(self, line):
        """
        Try to parse a line of text as a test result.

        Returns
        -------
        tuple of str or None
            If line represents a test result, then return a tuple with four
            strings: the name of the test function, the name of the test class,
            the test result, and the reason (if no reason is given, the fourth
            string is empty). Otherwise, return None.
        """
        regexp = (r'([^\d\W]\w*) \(([^\d\W][\w.]*)\) \.\.\. '
                  '(ok|FAIL|ERROR|skipped|expected failure|unexpected success)'
                  "( '([^']*)')?\Z")
        match = re.match(regexp, line)
        if match:
            msg = match.groups()[4] or ''
            return match.groups()[:3] + (msg, )
        else:
            return None

    def try_parse_exception_block(self, lines, line_index):
        """
        Try to parse a block detailing an exception in unittest output.

        Returns
        -------
        (int, str, str, list of str) or None
            If an exception block is parsed successfully, then return a tuple
            with the line index of the first line after the block, the name of
            the test function, the name of the test class, and the text of the
            exception. Otherwise, return None.
        """
        if not all(char == '=' for char in lines[line_index]):
            return None
        regexp = r'\w+: ([^\d\W]\w*) \(([^\d\W][\w.]*)\)\Z'
        match = re.match(regexp, lines[line_index + 1])
        if not match:
            return None
        if not all(char == '-' for char in lines[line_index + 2]):
            return None
        line_index += 3
        exception_text = []
        while lines[line_index]:
            exception_text.append(lines[line_index] + '\n')
            line_index += 1
        return (line_index, match.group(1), match.group(2), exception_text)
