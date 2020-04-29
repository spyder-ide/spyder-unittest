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
from spyder_unittest.backend.pytestworker import SpyderPlugin, main
from spyder_unittest.backend.zmqstream import ZmqStreamWriter

try:
    from unittest.mock import call, create_autospec, MagicMock, Mock
except ImportError:
    from mock import call, create_autospec, MagicMock, Mock  # Python 2


class EmptyClass:
    pass


@pytest.fixture
def plugin():
    mock_writer = create_autospec(ZmqStreamWriter)
    return SpyderPlugin(mock_writer)


@pytest.fixture
def plugin_ini():
    mock_writer = create_autospec(ZmqStreamWriter)
    plugin = SpyderPlugin(mock_writer)
    plugin.status = '---'
    plugin.duration = 0
    plugin.longrepr = []
    plugin.sections = []
    plugin.had_error = False
    plugin.was_skipped = False
    plugin.was_xfail = False
    return plugin


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
    report.longrepr = MagicMock()
    report.longrepr.__str__.return_value = 'message'
    plugin.pytest_collectreport(report)
    plugin.writer.write.assert_called_once_with({
        'event': 'collecterror',
        'nodeid': 'foo.py::bar',
        'longrepr': 'message'
    })


def test_spyderplugin_test_itemcollected(plugin):
    testitem = EmptyClass()
    testitem.nodeid = 'foo.py::bar'
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
    report.longrepr = None
    report.location = ('foo.py', 24, 'bar')
    return report


def test_pytest_runtest_logreport_passed(plugin_ini):
    report = standard_logreport()
    report.sections = ['output']
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.status == 'passed'
    assert plugin_ini.duration == 42
    assert plugin_ini.sections == ['output']
    assert plugin_ini.had_error is False
    assert plugin_ini.was_skipped is False
    assert plugin_ini.was_xfail is False


def test_pytest_runtest_logreport_failed(plugin_ini):
    report = standard_logreport()
    report.when = 'teardown'
    report.outcome = 'failed'
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.status == '---'
    assert plugin_ini.duration == 0
    assert plugin_ini.had_error is True
    assert plugin_ini.was_skipped is False
    assert plugin_ini.was_xfail is False


def test_pytest_runtest_logreport_skipped(plugin_ini):
    report = standard_logreport()
    report.when = 'setup'
    report.outcome = 'skipped'
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.status == '---'
    assert plugin_ini.duration == 0
    assert plugin_ini.had_error is False
    assert plugin_ini.was_skipped is True
    assert plugin_ini.was_xfail is False


@pytest.mark.parametrize('xfail_msg,longrepr', [
    ('msg', 'msg'),
    ('', 'WAS EXPECTED TO FAIL')
])
def test_pytest_runtest_logreport_xfail(plugin_ini, xfail_msg, longrepr):
    report = standard_logreport()
    report.wasxfail = xfail_msg
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.status == 'passed'
    assert plugin_ini.duration == 42
    assert plugin_ini.had_error is False
    assert plugin_ini.was_skipped is False
    assert plugin_ini.was_xfail is True
    assert plugin_ini.longrepr == [longrepr]


def test_pytest_runtest_logreport_with_reprcrash_longrepr(plugin_ini):
    class MockLongrepr:
        def __init__(self):
            self.reprcrash = EmptyClass()
            self.reprcrash.message = 'msg'

        def __str__(self):
            return 'reprtraceback'

    report = standard_logreport()
    report.longrepr = MockLongrepr()
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.longrepr == ['msg', 'reprtraceback']


def test_pytest_runtest_logreport_with_tuple_longrepr(plugin_ini):
    report = standard_logreport()
    report.longrepr = ('path', 'lineno', 'msg')
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.longrepr == ['msg']


def test_pytest_runtest_logreport_with_str_longrepr(plugin_ini):
    report = standard_logreport()
    report.longrepr = 'msg'
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.longrepr == ['msg']


def test_pytest_runtest_logreport_with_excinfo_longrepr(plugin_ini):
    class MockLongrepr:
        def __str__(self):
            return 'msg'

    report = standard_logreport()
    report.longrepr = MockLongrepr()
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.longrepr == ['msg']

@pytest.mark.parametrize('when,longrepr,expected',[
    ('setup', [], ['ERROR at setup: msg']),
    ('call', [], ['msg']),
    ('teardown', ['prev msg'], ['prev msg', 'ERROR at teardown: msg'])
])
def test_pytest_runtest_logreport_error_in_setup_or_teardown_message(
        plugin_ini, when, longrepr, expected):
    report = standard_logreport()
    report.when = when
    report.outcome = 'failed'
    report.longrepr = 'msg'
    plugin_ini.longrepr = longrepr
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.longrepr == expected


def test_pytest_runtest_logreport_error_in_setup_or_teardown_multiple_messages(
        plugin_ini):
    class MockLongrepr:
        def __init__(self):
            self.reprcrash = EmptyClass()
            self.reprcrash.message = 'msg'

        def __str__(self):
            return 'reprtraceback'

    report = standard_logreport()
    report.when = 'setup'
    report.outcome = 'failed'
    report.longrepr = MockLongrepr()
    plugin_ini.pytest_runtest_logreport(report)
    assert plugin_ini.longrepr == ['ERROR at setup: msg', 'reprtraceback']


def test_pytest_runtest_logfinish_skipped(plugin_ini):
    nodeid = 'foo.py::bar'
    location = ('foo.py', 24)
    plugin_ini.was_skipped = True
    plugin_ini.duration = 42
    plugin_ini.pytest_runtest_logfinish(nodeid, location)
    plugin_ini.writer.write.assert_called_once_with({
        'event': 'logreport',
        'outcome': 'skipped',
        'witherror': False,
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [],
        'filename': 'foo.py',
        'lineno': 24
    })


def test_pytest_runtest_logfinish_xfailed(plugin_ini):
    nodeid = 'foo.py::bar'
    location = ('foo.py', 24)
    plugin_ini.was_xfail = True
    plugin_ini.status = 'skipped'
    plugin_ini.duration = 42
    plugin_ini.pytest_runtest_logfinish(nodeid, location)
    plugin_ini.writer.write.assert_called_once_with({
        'event': 'logreport',
        'outcome': 'xfailed',
        'witherror': False,
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [],
        'filename': 'foo.py',
        'lineno': 24
    })


def test_pytest_runtest_logfinish_xpassed(plugin_ini):
    nodeid = 'foo.py::bar'
    location = ('foo.py', 24)
    plugin_ini.was_xfail = True
    plugin_ini.status = 'passed'
    plugin_ini.duration = 42
    plugin_ini.pytest_runtest_logfinish(nodeid, location)
    plugin_ini.writer.write.assert_called_once_with({
        'event': 'logreport',
        'outcome': 'xpassed',
        'witherror': False,
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [],
        'filename': 'foo.py',
        'lineno': 24
    })


@pytest.mark.parametrize('self_longrepr,message,longrepr', [
    (['msg1 line1'], 'msg1 line1', ''),
    (['msg1 line1\nmsg1 line2'], 'msg1 line1', 'msg1 line1\nmsg1 line2'),
    (['msg1 line1', 'msg2'], 'msg1 line1', 'msg2'),
    (['msg1 line1\nmsg1 line2', 'msg2'], 'msg1 line1',
     'msg1 line1\nmsg1 line2\nmsg2'),
])
def test_pytest_runtest_logfinish_handles_longrepr(plugin_ini, self_longrepr,
                                                   message, longrepr):
    nodeid = 'foo.py::bar'
    location = ('foo.py', 24)
    plugin_ini.status = 'passed'
    plugin_ini.duration = 42
    plugin_ini.longrepr = self_longrepr
    plugin_ini.pytest_runtest_logfinish(nodeid, location)
    plugin_ini.writer.write.assert_called_once_with({
        'event': 'logreport',
        'outcome': 'passed',
        'witherror': False,
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [],
        'filename': 'foo.py',
        'lineno': 24,
        'message': message,
        'longrepr': longrepr
    })


def test_pytestworker_integration(monkeypatch, tmpdir):
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath
    with open(testfilename, 'w') as f:
        f.write("def test_ok(): assert 1+1 == 2\n"
                "def test_fail(): assert 1+1 == 3\n")

    mock_writer = create_autospec(ZmqStreamWriter)
    MockZmqStreamWriter = Mock(return_value=mock_writer)
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestworker.ZmqStreamWriter',
        MockZmqStreamWriter)
    main(['mockscriptname', '42', testfilename])

    args = mock_writer.write.call_args_list

    assert args[0][0][0]['event'] == 'collected'
    assert args[0][0][0]['nodeid'] == 'test_foo.py::test_ok'

    assert args[1][0][0]['event'] == 'collected'
    assert args[1][0][0]['nodeid'] == 'test_foo.py::test_fail'

    assert args[2][0][0]['event'] == 'starttest'
    assert args[2][0][0]['nodeid'] == 'test_foo.py::test_ok'

    assert args[3][0][0]['event'] == 'logreport'
    assert args[3][0][0]['outcome'] == 'passed'
    assert args[3][0][0]['witherror'] is False
    assert args[3][0][0]['nodeid'] == 'test_foo.py::test_ok'
    assert args[3][0][0]['sections'] == []
    assert args[3][0][0]['filename'] == 'test_foo.py'
    assert args[3][0][0]['lineno'] == 0
    assert 'duration' in args[3][0][0]

    assert args[4][0][0]['event'] == 'starttest'
    assert args[4][0][0]['nodeid'] == 'test_foo.py::test_fail'

    assert args[5][0][0]['event'] == 'logreport'
    assert args[5][0][0]['outcome'] == 'failed'
    assert args[5][0][0]['witherror'] is False
    assert args[5][0][0]['nodeid'] == 'test_foo.py::test_fail'
    assert args[5][0][0]['sections'] == []
    assert args[5][0][0]['filename'] == 'test_foo.py'
    assert args[5][0][0]['lineno'] == 1
    assert 'duration' in args[5][0][0]
