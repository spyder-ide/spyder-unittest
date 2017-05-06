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
        olddata = None
        text = ""
        for line in output.splitlines():
            data = self.try_parse_result(line)
            if data:
                if olddata:
                    name = olddata[1] + '.' + olddata[0]
                    tr = TestResult(Category.OK, olddata[2], name, '', 0, text)
                    res.append(tr)
                olddata = data
                text = ""
            else:
                text += line + '\n'
        if olddata:
            name = olddata[1] + '.' + olddata[0]
            tr = TestResult(Category.OK, olddata[2], name, '', 0, text)
            res.append(tr)
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
        regexp = r'([^\d\W]\w*) \(([^\d\W][\w.]*)\) \.\.\. (ok)'
        match = re.fullmatch(regexp, line)
        print(repr(line), match)
        if match:
            return match.groups()
        else:
            return None
