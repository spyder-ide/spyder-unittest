# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Script for running py.test tests.

This script is meant to be run in a separate process by a PyTestRunner.
It runs tests via the py.test framework and prints the results so that the
PyTestRunner can read them.
"""

# Standard library imports
import io
import sys

# Third party imports
import pytest

# Local imports
from spyder_unittest.backend.jsonstream import JSONStreamWriter


class SpyderPlugin():
    """Pytest plugin which reports in format suitable for Spyder."""

    def __init__(self, writer):
        """Constructor."""
        self.writer = writer

    def pytest_itemcollected(self, item):
        """Called by py.test when a test item is collected."""
        self.writer.write({
            'event': 'collected',
            'name': item.name,
            'module': item.parent.name
        })

    def pytest_runtest_logreport(self, report):
        """Called by py.test when a (phase of a) test is completed."""
        if report.when in ['setup', 'teardown'] and report.outcome == 'passed':
            return
        self.writer.write({
            'event': 'logreport',
            'when': report.when,
            'outcome': report.outcome,
            'nodeid': report.nodeid})


def main(args):
    """Run py.test with the Spyder plugin."""
    old_stdout = sys.stdout
    stdout_buffer = io.StringIO()
    sys.stdout = stdout_buffer
    writer = JSONStreamWriter(old_stdout)
    pytest.main(args, plugins=[SpyderPlugin(writer)])
    # TODO Recover contents of stdout buffer and restore old stdout


if __name__ == '__main__':
    main(sys.argv[1:])
