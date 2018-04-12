# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Script for running pytest tests.

This script is meant to be run in a separate process by a PyTestRunner.
It runs tests via the pytest framework and prints the results so that the
PyTestRunner can read them.
"""

# Standard library imports
import sys

# Third party imports
import pytest

# Local imports
from spyder_unittest.backend.zmqstream import ZmqStreamWriter


class FileStub():
    """Stub for ZmqStreamWriter which instead writes to a file."""

    def __init__(self, filename):
        """Constructor; connect to specified filename."""
        self.file = open(filename, 'w')

    def write(self, obj):
        """Write Python object to file."""
        self.file.write(str(obj) + '\n')

    def close(self):
        """Close file."""
        self.file.close()


class SpyderPlugin():
    """Pytest plugin which reports in format suitable for Spyder."""

    def __init__(self, writer):
        """Constructor."""
        self.writer = writer

    def pytest_collectreport(self, report):
        """Called by pytest after collecting tests from a file."""
        if report.outcome == 'failed':
            self.writer.write({
                    'event': 'collecterror',
                    'nodeid': report.nodeid,
                    'longrepr': report.longrepr.longrepr
            })

    def pytest_itemcollected(self, item):
        """Called by pytest when a test item is collected."""
        nodeid = item.name
        x = item.parent
        while x.parent:
            nodeid = x.name + '::' + nodeid
            x = x.parent
        self.writer.write({
            'event': 'collected',
            'nodeid': nodeid
        })

    def pytest_runtest_logstart(self, nodeid, location):
        """Called by pytest before running a test."""
        self.writer.write({
            'event': 'starttest',
            'nodeid': nodeid
        })

    def pytest_runtest_logreport(self, report):
        """Called by pytest when a (phase of a) test is completed."""
        if report.when in ['setup', 'teardown'] and report.outcome == 'passed':
            return
        data = {'event': 'logreport',
                'when': report.when,
                'outcome': report.outcome,
                'nodeid': report.nodeid,
                'sections': report.sections,
                'duration': report.duration,
                'filename': report.location[0],
                'lineno': report.location[1]}
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
    """Run pytest with the Spyder plugin."""
    if args[1] == 'file':
        writer = FileStub('pytestworker.log')
    else:
        writer = ZmqStreamWriter(int(args[1]))
    pytest.main(args[2:], plugins=[SpyderPlugin(writer)])
    writer.close()


if __name__ == '__main__':
    main(sys.argv)
