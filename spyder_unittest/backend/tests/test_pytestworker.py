# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for pytestworker.py"""

# Standard library imports
import os

# Third party imports
import pytest

# Local imports
from spyder_unittest.backend.jsonstream import JSONStreamWriter
from spyder_unittest.backend.pytestworker import SpyderPlugin, main

try:
    from unittest.mock import call, create_autospec, Mock
except ImportError:
    from mock import call, create_autospec, Mock  # Python 2


class EmptyClass:
    pass


@pytest.fixture
def plugin():
    mock_writer = create_autospec(JSONStreamWriter)
    return SpyderPlugin(mock_writer)

def test_spyderplugin_test_collectreport_with_success(plugin):
    report = EmptyClass()
    report.outcome = 'success'
    report.nodeid = 'foo.py::bar'
    plugin.pytest_collectreport(report)
    plugin.writer.write.assert_not_called()

def test_spyderplugin_test_collectreport_with_failure(plugin):
    report = EmptyClass()
    report.outcome = 'failed'
    report.nodeid = 'foo.py::bar'
    report.longrepr = EmptyClass()
    report.longrepr.longrepr = 'message'
    plugin.pytest_collectreport(report)
    plugin.writer.write.assert_called_once_with({
        'event': 'collecterror',
        'nodeid': 'foo.py::bar',
        'longrepr': 'message'
    })

def test_spyderplugin_test_itemcollected(plugin):
    testitem = EmptyClass()
    testitem.name = 'bar'
    testitem.parent = EmptyClass()
    testitem.parent.name = 'foo.py'
    testitem.parent.parent = EmptyClass
    testitem.parent.parent.name = 'notused'
    testitem.parent.parent.parent = None
    plugin.pytest_itemcollected(testitem)
    plugin.writer.write.assert_called_once_with({
        'event': 'collected',
        'nodeid': 'foo.py::bar'
    })

def standard_logreport():
    report = EmptyClass()
    report.when = 'call'
    report.outcome = 'passed'
    report.nodeid = 'foo.py::bar'
    report.duration = 42
    report.sections = []
    report.longrepr = ''
    report.location = ('foo.py', 24, 'bar')
    return report

def test_spyderplugin_runtest_logreport(plugin):
    report = standard_logreport()
    plugin.pytest_runtest_logreport(report)
    plugin.writer.write.assert_called_once_with({
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [],
        'filename': 'foo.py',
        'lineno': 24
    })

def test_spyderplugin_runtest_logreport_passes_longrepr(plugin):
    report = standard_logreport()
    report.longrepr = 15
    plugin.pytest_runtest_logreport(report)
    plugin.writer.write.assert_called_once_with({
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [],
        'filename': 'foo.py',
        'lineno': 24,
        'longrepr': '15'
    })

def test_spyderplugin_runtest_logreport_with_longrepr_tuple(plugin):
    report = standard_logreport()
    report.longrepr = ('ham', 'spam')
    plugin.pytest_runtest_logreport(report)
    plugin.writer.write.assert_called_once_with({
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [],
        'filename': 'foo.py',
        'lineno': 24,
        'longrepr': ('ham', 'spam')
    })

def test_spyderplugin_runtest_logreport_passes_wasxfail(plugin):
    report = standard_logreport()
    report.wasxfail = ''
    plugin.pytest_runtest_logreport(report)
    plugin.writer.write.assert_called_once_with({
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [],
        'filename': 'foo.py',
        'lineno': 24,
        'wasxfail': ''
    })

def test_spyderplugin_runtest_logreport_passes_message(plugin):
    class MockLongrepr:
        def __init__(self):
            self.reprcrash = EmptyClass()
            self.reprcrash.message = 'msg'
        def __str__(self):
            return 'text'

    report = standard_logreport()
    report.longrepr = MockLongrepr()
    plugin.pytest_runtest_logreport(report)
    plugin.writer.write.assert_called_once_with({
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [],
        'filename': 'foo.py',
        'lineno': 24,
        'longrepr': 'text',
        'message': 'msg'
    })

def test_spyderplugin_runtest_logreport_ignores_teardown_passed(plugin):
    report = standard_logreport()
    report.when = 'teardown'
    plugin.pytest_runtest_logreport(report)
    plugin.writer.write.assert_not_called()

def test_main_captures_stdout_and_stderr(monkeypatch):
    def mock_main(args, plugins):
        print('output')
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestworker.pytest.main', mock_main)

    mock_writer = create_autospec(JSONStreamWriter)
    MockJSONStreamWriter = Mock(return_value=mock_writer)
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestworker.JSONStreamWriter',
        MockJSONStreamWriter)

    main(None)
    mock_writer.write.assert_called_once_with({
            'event': 'finished', 'stdout': 'output\n'})

def test_pytestworker_integration(monkeypatch, tmpdir):
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath
    with open(testfilename, 'w') as f:
        f.write("def test_ok(): assert 1+1 == 2\n"
                "def test_fail(): assert 1+1 == 3\n")

    mock_writer = create_autospec(JSONStreamWriter)
    MockJSONStreamWriter = Mock(return_value=mock_writer)
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestworker.JSONStreamWriter',
        MockJSONStreamWriter)
    main([testfilename])

    args = mock_writer.write.call_args_list

    assert args[0][0][0]['event'] == 'collected'
    assert args[0][0][0]['nodeid'] == 'test_foo.py::test_ok'

    assert args[1][0][0]['event'] == 'collected'
    assert args[1][0][0]['nodeid'] == 'test_foo.py::test_fail'

    assert args[2][0][0]['event'] == 'starttest'
    assert args[2][0][0]['nodeid'] == 'test_foo.py::test_ok'

    assert args[3][0][0]['event'] == 'logreport'
    assert args[3][0][0]['when'] == 'call'
    assert args[3][0][0]['outcome'] == 'passed'
    assert args[3][0][0]['nodeid'] == 'test_foo.py::test_ok'
    assert args[3][0][0]['sections'] == []
    assert args[3][0][0]['filename'] == 'test_foo.py'
    assert args[3][0][0]['lineno'] == 0
    assert 'duration' in args[3][0][0]

    assert args[4][0][0]['event'] == 'starttest'
    assert args[4][0][0]['nodeid'] == 'test_foo.py::test_fail'

    assert args[5][0][0]['event'] == 'logreport'
    assert args[5][0][0]['when'] == 'call'
    assert args[5][0][0]['outcome'] == 'failed'
    assert args[5][0][0]['nodeid'] == 'test_foo.py::test_fail'
    assert args[5][0][0]['sections'] == []
    assert args[5][0][0]['filename'] == 'test_foo.py'
    assert args[5][0][0]['lineno'] == 1
    assert 'duration' in args[5][0][0]

    assert args[6][0][0]['event'] == 'finished'
    assert 'pytest' in args[6][0][0]['stdout']
