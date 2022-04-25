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

# Local imports, needs to not be absolute otherwise it will fail if trying
# to execute in a different env with only spyder-kernel installed
try:
    # this line is needed for the pytests to succeed
    from .zmqstream import ZmqStreamWriter
except:
    # this line is needed for the plugin to work
    from zmqstream import ZmqStreamWriter

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

    def initialize_logreport(self):
        """Reset accumulator variables."""
        self.status = '---'
        self.duration = 0
        self.longrepr = []
        self.sections = []
        self.had_error = False
        self.was_skipped = False
        self.was_xfail = False

    def pytest_report_header(self, config, startdir):
        """Called by pytest before any reporting."""
        self.writer.write({
            'event': 'config',
            'rootdir': str(config.rootdir)
        })

    def pytest_collectreport(self, report):
        """Called by pytest after collecting tests from a file."""
        if report.outcome == 'failed':
            self.writer.write({
                    'event': 'collecterror',
                    'nodeid': report.nodeid,
                    'longrepr': str(report.longrepr)
            })

    def pytest_itemcollected(self, item):
        """Called by pytest when a test item is collected."""
        self.writer.write({
            'event': 'collected',
            'nodeid': item.nodeid
        })

    def pytest_runtest_logstart(self, nodeid, location):
        """Called by pytest before running a test."""
        self.writer.write({
            'event': 'starttest',
            'nodeid': nodeid
        })
        self.initialize_logreport()

    def pytest_runtest_logreport(self, report):
        """Called by pytest when a phase of a test is completed."""
        if report.when == 'call':
            self.status = report.outcome
            self.duration = report.duration
        else:
            if report.outcome == 'failed':
                self.had_error = True
            elif report.outcome == 'skipped':
                self.was_skipped = True
        if hasattr(report, 'wasxfail'):
            self.was_xfail = True
            self.longrepr.append(report.wasxfail if report.wasxfail else 
                'WAS EXPECTED TO FAIL')
        self.sections = report.sections  # already accumulated over phases
        if report.longrepr:
            first_msg_idx = len(self.longrepr)
            if hasattr(report.longrepr, 'reprcrash'):
                self.longrepr.append(report.longrepr.reprcrash.message)
            if isinstance(report.longrepr, tuple):
                self.longrepr.append(report.longrepr[2])
            elif isinstance(report.longrepr, str):
                self.longrepr.append(report.longrepr)
            else:
                self.longrepr.append(str(report.longrepr))
            if report.outcome == 'failed' and report.when in (
                    'setup', 'teardown'):
                self.longrepr[first_msg_idx] = '{} {}: {}'.format(
                    'ERROR at', report.when, self.longrepr[first_msg_idx])

    def pytest_runtest_logfinish(self, nodeid, location):
        """Called by pytest when the entire test is completed."""
        if self.was_xfail:
            if self.status == 'passed':
                self.status = 'xpassed'
            else: # 'skipped'
                self.status = 'xfailed'
        elif self.was_skipped:
            self.status = 'skipped'
        data = {'event': 'logreport',
                'outcome': self.status,
                'witherror': self.had_error,
                'sections': self.sections,
                'duration': self.duration,
                'nodeid': nodeid,
                'filename': location[0],
                'lineno': location[1]}
        if self.longrepr:
            msg_lines = self.longrepr[0].rstrip().splitlines()
            data['message'] = msg_lines[0]
            start_item = 1 if len(msg_lines) == 1 else 0
            data['longrepr'] = '\n'.join(self.longrepr[start_item:])
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
