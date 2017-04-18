# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for unittest framework."""

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
        Read and parse unit test results.

        Returns
        -------
        list of TestResult
            Unit test results.
        """
        return [TestResult(Category.OK, '', 'all', '', 0, output)]
