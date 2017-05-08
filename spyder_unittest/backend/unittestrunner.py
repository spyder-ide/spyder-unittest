# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for unittest framework."""

# Standard library imports
import re

# Third party imports
from qtpy.QtCore import QTextCodec
from spyder.py3compat import to_text_string

# Local imports
from spyder_unittest.backend.runnerbase import Category, RunnerBase, TestResult


class UnittestRunner(RunnerBase):
    """Class for running tests with unittest module in standard library."""

    executable = 'python'

    def create_argument_list(self):
        """Create argument list for testing process."""
        return ['-m', 'unittest', '-v']

    def finished(self):
        """
        Called when the unit test process has finished.

        This function reads the results and emits `sig_finished`.
        """
        qbytearray = self.process.readAllStandardOutput()
        locale_codec = QTextCodec.codecForLocale()
        output = to_text_string(locale_codec.toUnicode(qbytearray.data()))
        testresults = self.load_data(output)  # overrides base class method
        self.sig_finished.emit(testresults, output)

    def load_data(self, output):
        """
        Read and parse output from unittest module.

        Returns
        -------
        list of TestResult
            Unit test results.
        """
        res = []
        lines = output.splitlines()
        line_index = 0
        while line_index < len(lines):
            data = self.try_parse_result(lines[line_index])
            if data:
                name = data[1] + '.' + data[0]
                cat = Category.OK if data[2] == 'ok' else Category.FAIL
                tr = TestResult(cat, data[2], name, '', 0, '')
                res.append(tr)
            elif self.try_parse_footer(lines, line_index):
                line_index += 5
                continue
            elif res:
                text = res[-1].extra_text + lines[line_index] + '\n'
                res[-1] = res[-1]._replace(extra_text=text)
            line_index += 1
        return res

    def try_parse_result(self, line):
        """
        Try to parse a line of text as a test result.

        Returns
        -------
        tuple of str or None
            If line represents a test result, then return a tuple with three
            strings: the name of the test function, the name of the test class,
            and the test result. Otherwise, return None.
        """
        regexp = r'([^\d\W]\w*) \(([^\d\W][\w.]*)\) \.\.\. (ok|FAIL|ERROR)'
        match = re.fullmatch(regexp, line)
        if match:
            return match.groups()
        else:
            return None

    def try_parse_footer(self, lines, line_index):
        """
        Try to parse footer of unittest output.

        Returns
        -------
        bool
            True if footer is parsed successfully, False otherwise
        """
        if lines[line_index] != '':
            return False
        if not all(char == '-' for char in lines[line_index + 1]):
            return False
        if not re.match(r'^Ran [\d]+ tests? in', lines[line_index + 2]):
            return False
        if lines[line_index + 3] != '':
            return False
        return True
