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


class StdoutBuffer(io.TextIOWrapper):
    """
    Wrapper for binary stream which accepts both text and binary strings.

    Source: https://stackoverflow.com/a/19344871
    """

    def write(self, string):
        """Write text or binary string to underlying stream."""
        try:
            return super(StdoutBuffer, self).write(string)
        except TypeError:
            # redirect encoded byte strings directly to buffer
            return super(StdoutBuffer, self).buffer.write(string)


class SpyderPlugin():
    """Pytest plugin which reports in format suitable for Spyder."""

    def __init__(self, writer):
        """Constructor."""
        self.writer = writer

    def pytest_collectreport(self, report):
        """Called by py.test after collecting tests from a file."""
        if report.outcome == 'failed':
            self.writer.write({
                    'event': 'collecterror',
                    'nodeid': report.nodeid,
                    'longrepr': report.longrepr.longrepr
            })

    def pytest_itemcollected(self, item):
        """Called by py.test when a test item is collected."""
        self.writer.write({
            'event': 'collected',
            'name': item.name,
            'module': item.parent.name
        })

    def pytest_runtest_logstart(self, nodeid, location):
        """Called by py.test before running a test."""
        self.writer.write({
            'event': 'starttest',
            'nodeid': nodeid
        })

    def pytest_runtest_logreport(self, report):
        """Called by py.test when a (phase of a) test is completed."""
        if report.when in ['setup', 'teardown'] and report.outcome == 'passed':
            return
        # print(report.__dict__)
        data = {'event': 'logreport',
                'when': report.when,
                'outcome': report.outcome,
                'nodeid': report.nodeid,
                'sections': report.sections,
                'duration': report.duration}
        if report.longrepr:
            if isinstance(report.longrepr, tuple):
                data['longrepr'] = report.longrepr
            else:
                data['longrepr'] = str(report.longrepr)
        if hasattr(report, 'wasxfail'):
            data['wasxfail'] = report.wasxfail
        if hasattr(report.longrepr, 'reprcrash'):
            data['message'] = report.longrepr.reprcrash.message
        self.writer.write(data)


def main(args):
    """Run py.test with the Spyder plugin."""
    old_stdout = sys.stdout
    stdout_buffer = StdoutBuffer(io.BytesIO(), sys.stdout.encoding)
    sys.stdout = stdout_buffer

    writer = JSONStreamWriter(old_stdout)
    pytest.main(args, plugins=[SpyderPlugin(writer)])

    stdout_buffer.seek(0)
    data = {'event': 'finished', 'stdout': stdout_buffer.read()}
    writer.write(data)
    sys.stdout = old_stdout


if __name__ == '__main__':
    main(sys.argv[1:])
