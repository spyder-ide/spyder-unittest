# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for unittest framework."""

# Standard library imports
import re
import subprocess

# Local imports
from spyder_unittest.backend.runnerbase import Category, RunnerBase, TestResult


class UnittestRunner(RunnerBase):
    """Class for running tests with unittest module in standard library."""

    module = 'unittest'
    name = 'unittest'

    def __init__(self, widget, resultfilename=None):
        super().__init__(widget, resultfilename)
        # Set a sensible default
        self.fullname_version = 'pre311'

    def create_argument_list(self, config, cov_path):
        """Create argument list for testing process."""
        return ['-m', self.module, 'discover', '-v']

    def finished(self):
        """
        Called when the unit test process has finished.

        This function reads the results and emits `sig_finished`.
        """
        self.set_fullname_version()
        output = self.read_all_process_output()
        testresults = self.load_data(output)
        self.sig_finished.emit(testresults, output, True)

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

        try:
            while lines[line_index]:
                data = self.try_parse_result(lines, line_index)
                if data:
                    line_index = data[0]
                    if data[2] == 'ok':
                        cat = Category.OK
                    elif data[2] == 'FAIL' or data[2] == 'ERROR':
                        cat = Category.FAIL
                    else:
                        cat = Category.SKIP
                    tr = TestResult(category=cat, status=data[2], name=data[1],
                                    message=data[3])
                    res.append(tr)
                else:
                    line_index += 1

            line_index += 1
            while not (lines[line_index]
                       and all(c == '-' for c in lines[line_index])):
                data = self.try_parse_exception_block(lines, line_index)
                if data:
                    line_index = data[0]
                    test_index = next(
                        i for i, tr in enumerate(res)
                        if tr.name == data[1])
                    res[test_index].extra_text = data[2]
                else:
                    line_index += 1
        except IndexError:
            pass

        return res

    def try_parse_result(self, lines, line_index):
        """
        Try to parse one or more lines of text as a test result.

        Returns
        -------
        (int, str, str, str) or None
            If a test result is parsed successfully then return a tuple with
            the line index of the first line after the test result, the full
            name of the test function (including the class), the test result,
            and the reason (if no reason is given, the third string is empty).
            Otherwise, return None.
        """
        regexp = r'([^\d\W]\w*) \(([^\d\W][\w.]*)\)'
        match = re.match(regexp, lines[line_index])
        if match:
            function_fullname = self.get_fullname(match.group(1), match.group(2))
        else:
            return None
        while lines[line_index]:
            regexp = (r' \.\.\. (ok|FAIL|ERROR|skipped|expected failure|'
                      r"unexpected success)( '([^']*)')?\Z")
            match = re.search(regexp, lines[line_index])
            if match:
                result = match.group(1)
                msg = match.group(3) or ''
                return (line_index + 1, function_fullname, result, msg)
            line_index += 1
        return None

    def try_parse_exception_block(self, lines, line_index):
        """
        Try to parse a block detailing an exception in unittest output.

        Returns
        -------
        (int, str, list of str) or None
            If an exception block is parsed successfully, then return a tuple
            with the line index of the first line after the block, the full
            name of the test function (including the class), and the text of
            the exception. Otherwise, return None.
        """
        if not all(char == '=' for char in lines[line_index]):
            return None
        regexp = r'\w+: ([^\d\W]\w*) \(([^\d\W][\w.]*)\)\Z'
        match = re.match(regexp, lines[line_index + 1])
        if not match:
            return None
        line_index += 1
        while not all(char == '-' for char in lines[line_index]):
            if not lines[line_index]:
                return None
            line_index += 1
        line_index += 1
        exception_text = []
        while lines[line_index]:
            exception_text.append(lines[line_index])
            line_index += 1
        function_fullname = self.get_fullname(match.group(1), match.group(2))
        return (line_index, function_fullname, exception_text)

    def set_fullname_version(self):
        script = 'import platform; print(platform.python_version())'
        process = subprocess.run([self.executable, '-c', script],
                                 capture_output=True, text=True)
        if process.returncode != 0:
            self.fullname_version = 'pre311'
            return

        # We only take the first two components as the third might
        # be something like '0a3'.
        exec_version_components = process.stdout.split('.')[:2]
        exec_version = tuple(map(int, exec_version_components))
        if exec_version < (3, 11):
            self.fullname_version = 'pre311'
        else:
            self.fullname_version = '311'

    def get_fullname(self, fn_name, parenthesised):
        """
        Determine the test name output by unittest.

        Up to Python 3.10, unittest output read:
        test_fail (testing.test_unittest.MyTest) ... FAIL
        but from Python 3.11, it reads:
        test_fail (testing.test_unittest.MyTest.test_fail) ... FAIL

        Parameters
        ----------
        fn_name : str
            Part prior to the parentheses (without spaces)
        parenthesised : str
            Part within the parentheses

        Returns
        -------
        fullname : str
            The full name of the class plus function,
            "testing.test_unittest.MyTest.test_fail" in the above
            example.
        """
        if self.fullname_version == 'pre311':
            function_fullname = '{}.{}'.format(parenthesised, fn_name)
        else:
            function_fullname = parenthesised
        return function_fullname
