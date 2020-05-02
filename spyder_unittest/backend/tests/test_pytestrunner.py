# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for pytestrunner.py"""

# Standard library imports
import os
import os.path as osp

# Third party imports
from qtpy.QtCore import QByteArray

# Local imports
from spyder_unittest.backend.pytestrunner import (PyTestRunner,
                                                  logreport_to_testresult)
from spyder_unittest.backend.runnerbase import Category, TestResult
from spyder_unittest.widgets.configdialog import Config

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


def test_pytestrunner_is_installed():
    assert PyTestRunner(None).is_installed()


def test_pytestrunner_create_argument_list(monkeypatch):
    MockZMQStreamReader = Mock()
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestrunner.ZmqStreamReader',
        MockZMQStreamReader)
    mock_reader = MockZMQStreamReader()
    mock_reader.port = 42
    runner = PyTestRunner(None, 'results')
    runner.reader = mock_reader
    monkeypatch.setattr('spyder_unittest.backend.pytestrunner.os.path.dirname',
                        lambda _: 'dir')
    pyfile, port = runner.create_argument_list()
    assert pyfile == 'dir{}pytestworker.py'.format(os.sep)
    assert port == '42'


def test_pytestrunner_start(monkeypatch):
    MockZMQStreamReader = Mock()
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestrunner.ZmqStreamReader',
        MockZMQStreamReader)
    mock_reader = MockZMQStreamReader()

    MockRunnerBase = Mock(name='RunnerBase')
    monkeypatch.setattr('spyder_unittest.backend.pytestrunner.RunnerBase',
                        MockRunnerBase)

    runner = PyTestRunner(None, 'results')
    config = Config()
    runner.start(config, ['pythondir'])
    assert runner.config is config
    assert runner.reader is mock_reader
    runner.reader.sig_received.connect.assert_called_once_with(
        runner.process_output)
    MockRunnerBase.start.assert_called_once_with(runner, config, ['pythondir'])


def test_pytestrunner_process_output_with_collected(qtbot):
    runner = PyTestRunner(None)
    output = [{'event': 'collected', 'nodeid': 'spam.py::ham'},
              {'event': 'collected', 'nodeid': 'eggs.py::bacon'}]
    with qtbot.waitSignal(runner.sig_collected) as blocker:
        runner.process_output(output)
    expected = ['spam.ham', 'eggs.bacon']
    assert blocker.args == [expected]

def test_pytestrunner_process_output_with_collecterror(qtbot):
    runner = PyTestRunner(None)
    output = [{
            'event': 'collecterror',
            'nodeid': 'ham/spam.py',
            'longrepr': 'msg'
    }]
    with qtbot.waitSignal(runner.sig_collecterror) as blocker:
        runner.process_output(output)
    expected = [('ham.spam', 'msg')]
    assert blocker.args == [expected]

def test_pytestrunner_process_output_with_starttest(qtbot):
    runner = PyTestRunner(None)
    output = [{'event': 'starttest', 'nodeid': 'ham/spam.py::ham'},
              {'event': 'starttest', 'nodeid': 'ham/eggs.py::bacon'}]
    with qtbot.waitSignal(runner.sig_starttest) as blocker:
        runner.process_output(output)
    expected = ['ham.spam.ham', 'ham.eggs.bacon']
    assert blocker.args == [expected]

def standard_logreport_output():
    return {
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'filename': 'foo.py',
        'lineno': 24,
        'duration': 42
    }

def test_pytestrunner_process_output_with_logreport_passed(qtbot):
    runner = PyTestRunner(None)
    runner.config = Config(wdir='ham')
    output = [standard_logreport_output()]
    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)
    expected = [TestResult(Category.OK, 'ok', 'foo.bar', time=42,
                           filename=osp.join('ham', 'foo.py'), lineno=24)]
    assert blocker.args == [expected]

def test_logreport_to_testresult_passed():
    report = standard_logreport_output()
    expected = TestResult(Category.OK, 'ok', 'foo.bar', time=42,
                          filename=osp.join('ham', 'foo.py'), lineno=24)
    assert logreport_to_testresult(report, Config(wdir='ham')) == expected

def test_logreport_to_testresult_failed():
    report = standard_logreport_output()
    report['outcome'] = 'failed'
    report['message'] = 'msg'
    report['longrepr'] = 'exception text'
    expected = TestResult(Category.FAIL, 'failure', 'foo.bar',
                          message='msg', time=42, extra_text='exception text',
                          filename=osp.join('ham', 'foo.py'), lineno=24)
    assert logreport_to_testresult(report, Config(wdir='ham')) == expected

def test_logreport_to_testresult_skipped():
    report = standard_logreport_output()
    report['when'] = 'setup'
    report['outcome'] = 'skipped'
    report['longrepr'] = ('file', 24, 'skipmsg')
    expected = TestResult(Category.SKIP, 'skipped', 'foo.bar',
                          time=42, extra_text='skipmsg',
                          filename=osp.join('ham', 'foo.py'), lineno=24)
    assert logreport_to_testresult(report, Config(wdir='ham')) == expected

def test_logreport_to_testresult_xfail():
    report = standard_logreport_output()
    report['outcome'] = 'skipped'
    report['message'] = 'msg'
    report['longrepr'] = 'exception text'
    report['wasxfail'] = ''
    expected = TestResult(Category.SKIP, 'skipped', 'foo.bar',
                          message='msg', time=42, extra_text='exception text',
                          filename=osp.join('ham', 'foo.py'), lineno=24)
    assert logreport_to_testresult(report, Config(wdir='ham')) == expected

def test_logreport_to_testresult_xpass():
    report = standard_logreport_output()
    report['wasxfail'] = ''
    expected = TestResult(Category.OK, 'ok', 'foo.bar', time=42,
                          filename=osp.join('ham', 'foo.py'), lineno=24)
    assert logreport_to_testresult(report, Config(wdir='ham')) == expected

def test_logreport_to_testresult_with_output():
    report = standard_logreport_output()
    report['sections'] = [['Captured stdout call', 'ham\n'],
                          ['Captured stderr call', 'spam\n']]
    txt = ('----- Captured stdout call -----\nham\n'
           '----- Captured stderr call -----\nspam\n')
    expected = TestResult(Category.OK, 'ok', 'foo.bar', time=42,
                          extra_text=txt, filename=osp.join('ham', 'foo.py'),
                          lineno=24)
    assert logreport_to_testresult(report, Config(wdir='ham')) == expected


def test_get_versions_without_plugins(monkeypatch):
    import pytest
    monkeypatch.setattr(pytest, '__version__', '1.2.3')
    from _pytest.config import PytestPluginManager
    monkeypatch.setattr(
        PytestPluginManager,
        'list_plugin_distinfo', lambda _: ())

    runner = PyTestRunner(None)
    assert runner.get_versions() == ['pytest 1.2.3']


def test_get_versions_with_plugins(monkeypatch):
    import pytest
    import pkg_resources
    monkeypatch.setattr(pytest, '__version__', '1.2.3')
    dist1 = pkg_resources.Distribution(project_name='myPlugin1',
                                       version='4.5.6')
    dist2 = pkg_resources.Distribution(project_name='myPlugin2',
                                       version='7.8.9')
    from _pytest.config import PytestPluginManager
    monkeypatch.setattr(
        PytestPluginManager,
        'list_plugin_distinfo', lambda _: (('1', dist1), ('2', dist2)))
    runner = PyTestRunner(None)
    assert runner.get_versions() == ['pytest 1.2.3', '   myPlugin1 4.5.6',
                                     '   myPlugin2 7.8.9']
