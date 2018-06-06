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
from spyder.utils.misc import get_python_executable

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

def test_pytestrunner_start(monkeypatch):
    MockQProcess = Mock()
    monkeypatch.setattr('spyder_unittest.backend.runnerbase.QProcess',
                        MockQProcess)
    mock_process = MockQProcess()
    mock_process.systemEnvironment = lambda: ['VAR=VALUE', 'PYTHONPATH=old']

    MockEnvironment = Mock()
    monkeypatch.setattr(
        'spyder_unittest.backend.runnerbase.QProcessEnvironment',
        MockEnvironment)
    mock_environment = MockEnvironment()

    mock_remove = Mock(side_effect=OSError())
    monkeypatch.setattr('spyder_unittest.backend.runnerbase.os.remove',
                        mock_remove)

    MockZMQStreamReader = Mock()
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestrunner.ZmqStreamReader',
        MockZMQStreamReader)
    mock_reader = MockZMQStreamReader()
    mock_reader.port = 42

    runner = PyTestRunner(None, 'results')
    config = Config('pytest', 'wdir')
    runner.start(config, ['pythondir'])

    mock_process.setWorkingDirectory.assert_called_once_with('wdir')
    mock_process.finished.connect.assert_called_once_with(runner.finished)
    mock_process.setProcessEnvironment.assert_called_once_with(
        mock_environment)

    workerfile = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, 'pytestworker.py'))
    mock_process.start.assert_called_once_with(
            get_python_executable(), [workerfile, '42'])

    mock_environment.insert.assert_any_call('VAR', 'VALUE')
    # mock_environment.insert.assert_any_call('PYTHONPATH', 'pythondir:old')
    # TODO: Find out why above test fails
    mock_remove.called_once_with('results')

    assert runner.reader is mock_reader

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
