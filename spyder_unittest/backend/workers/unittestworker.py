# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Script for running unittest tests.

This script is meant to be run in a separate process by a UnittestRunner.
It runs tests via the unittest framework and transmits the results over a ZMQ
socket so that the UnittestRunner can read them.

Usage: python unittestworker.py port

Here, port is the port number of the ZMQ socket. Use `file` to store the
results in the file `unittestworker.json`.
"""

from __future__ import annotations

# Standard library imports
import sys
from typing import ClassVar
from unittest import (
    defaultTestLoader, TestCase, TestSuite, TextTestResult, TextTestRunner)

# Local imports
# Note that the script can be run in an environment that does not contain
# spyder_unittest so `from spyder_unittest.xxx import xxx` does not work.
from zmqwriter import FileStub, ZmqStreamWriter


class SpyderTestResult(TextTestResult):
    """
    Store test results and write them to a ZmqStreamWriter.

    The member `.writer` should be set to a ZmqStreamWriter before
    running any tests.
    """

    writer: ClassVar[ZmqStreamWriter]

    def startTest(self, test: TestCase) -> None:
        self.writer.write({
            'event': 'startTest',
            'id': test.id()
        })
        super().startTest(test)

    def addSuccess(self, test: TestCase) -> None:
        self.writer.write({
            'event': 'addSuccess',
            'id': test.id()
        })
        super().addSuccess(test)

    def addError(self, test: TestCase, err) -> None:
        (__, value, __) = err
        first_line = str(value).splitlines()[0]
        self.writer.write({
            'event': 'addError',
            'id': test.id(),
            'reason': f'{type(value).__name__}: {first_line}',
            'err': self._exc_info_to_string(err, test)
        })
        super().addError(test, err)

    def addFailure(self, test: TestCase, err) -> None:
        (__, value, __) = err
        first_line = str(value).splitlines()[0]
        self.writer.write({
            'event': 'addFailure',
            'id': test.id(),
            'reason': f'{type(value).__name__}: {first_line}',
            'err': self._exc_info_to_string(err, test)
        })
        super().addFailure(test, err)

    def addSkip(self, test: TestCase, reason: str) -> None:
        self.writer.write({
            'event': 'addSkip',
            'id': test.id(),
            'reason': reason
        })
        super().addSkip(test, reason)

    def addExpectedFailure(self, test: TestCase, err) -> None:
        (__, value, __) = err
        first_line = str(value).splitlines()[0]
        self.writer.write({
            'event': 'addExpectedFailure',
            'id': test.id(),
            'reason': f'{type(value).__name__}: {first_line}',
            'err': self._exc_info_to_string(err, test)
        })
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test: TestCase) -> None:
        self.writer.write({
            'event': 'addUnexpectedSuccess',
            'id': test.id()
        })
        super().addUnexpectedSuccess(test)


def report_collected(writer: ZmqStreamWriter, test_suite: TestSuite) -> None:
    for test in test_suite:
        if isinstance(test, TestSuite):
            report_collected(writer, test)
        else:
            writer.write({
                'event': 'collected',
                'id': test.id()
            })


def main(args: list[str]) -> None:
    """Run unittest tests."""
    # Parse command line arguments and create writer
    if args[1] != 'file':
        writer = ZmqStreamWriter(args[1])
    else:
        writer = FileStub('unittestworker.log')
    SpyderTestResult.writer = writer

    # Gather tests
    test_suite = defaultTestLoader.discover('.')
    report_collected(writer, test_suite)

    # Run tests
    test_runner = TextTestRunner(verbosity=2, resultclass=SpyderTestResult)
    test_runner.run(test_suite)
    writer.close()


if __name__ == '__main__':
    main(sys.argv)
