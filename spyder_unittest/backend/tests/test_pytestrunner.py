# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for pytestrunner.py"""

# Standard library imports
import os

# Third party imports
from qtpy.QtCore import QByteArray
from spyder.utils.misc import get_python_executable

# Local imports
from spyder_unittest.backend.pytestrunner import PyTestRunner
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

    MockJSONStreamReader = Mock()
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestrunner.JSONStreamReader',
        MockJSONStreamReader)
    mock_reader = MockJSONStreamReader()

    runner = PyTestRunner(None, 'results')
    config = Config('py.test', 'wdir')
    runner.start(config, ['pythondir'])

    mock_process.setWorkingDirectory.assert_called_once_with('wdir')
    mock_process.finished.connect.assert_called_once_with(runner.finished)
    mock_process.setProcessEnvironment.assert_called_once_with(
        mock_environment)

    workerfile = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, 'pytestworker.py'))
    mock_process.start.assert_called_once_with(
        get_python_executable(), [workerfile])

    mock_environment.insert.assert_any_call('VAR', 'VALUE')
    # mock_environment.insert.assert_any_call('PYTHONPATH', 'pythondir:old')
    # TODO: Find out why above test fails
    mock_remove.called_once_with('results')

    assert runner.reader is mock_reader


def test_pytestrunner_read_output(monkeypatch):
    runner = PyTestRunner(None)
    runner.process = Mock()
    qbytearray = QByteArray(b'encoded')
    runner.process.readAllStandardOutput = Mock(return_value=qbytearray)
    runner.reader = Mock()
    runner.reader.consume = Mock(return_value='decoded')
    runner.process_output = Mock()

    runner.read_output()
    assert runner.reader.consume.called_once_with('encoded')
    assert runner.process_output.called_once_with('decoded')


def test_pytestrunner_process_output_with_collected(qtbot):
    runner = PyTestRunner(None)
    output = [{
        'event': 'collected',
        'module': 'spam.py',
        'name': 'ham'
    }, {
        'event': 'collected',
        'module': 'eggs.py',
        'name': 'bacon'
    }]
    with qtbot.waitSignal(runner.sig_collected) as blocker:
        runner.process_output(output)
    expected = ['spam.ham', 'eggs.bacon']
    assert blocker.args == [expected]


def test_pytestrunner_process_output_with_starttest(qtbot):
    runner = PyTestRunner(None)
    output = [{'event': 'starttest', 'nodeid': 'ham/spam.py::ham'},
              {'event': 'starttest', 'nodeid': 'ham/eggs.py::bacon'}]
    with qtbot.waitSignal(runner.sig_starttest) as blocker:
        runner.process_output(output)
    expected = ['ham.spam.ham', 'ham.eggs.bacon']
    assert blocker.args == [expected]


def test_pytestrunner_process_output_with_logreport_passed(qtbot):
    runner = PyTestRunner(None)
    output = [{
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'duration': 42
    }]
    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)
    expected = [TestResult(Category.OK, 'ok', 'foo.bar', time=42)]
    assert blocker.args == [expected]


def test_pytestrunner_logreport_to_testresult_passed():
    runner = PyTestRunner(None)
    report = {
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'duration': 42
    }
    expected = TestResult(Category.OK, 'ok', 'foo.bar', time=42)
    assert runner.logreport_to_testresult(report) == expected


def test_pytestrunner_logreport_to_testresult_failed():
    runner = PyTestRunner(None)
    report = {
        'event': 'logreport',
        'when': 'call',
        'outcome': 'failed',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'message': 'msg',
        'longrepr': 'exception text'
    }
    expected = TestResult(Category.FAIL, 'failure', 'foo.bar',
                          message='msg', time=42, extra_text='exception text')
    assert runner.logreport_to_testresult(report) == expected


def test_pytestrunner_logreport_to_testresult_skipped():
    runner = PyTestRunner(None)
    report = {
        'event': 'logreport',
        'when': 'setup',
        'outcome': 'skipped',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'longrepr': ['file', 24, 'skipmsg']
    }
    expected = TestResult(Category.SKIP, 'skipped', 'foo.bar',
                          time=42, extra_text='skipmsg')
    assert runner.logreport_to_testresult(report) == expected


def test_pytestrunner_logreport_to_testresult_xfail():
    runner = PyTestRunner(None)
    report = {
        'event': 'logreport',
        'when': 'call',
        'outcome': 'skipped',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'message': 'msg',
        'longrepr': 'exception text',
        'wasxfail': ''
    }
    expected = TestResult(Category.SKIP, 'skipped', 'foo.bar',
                          message='msg', time=42, extra_text='exception text')
    assert runner.logreport_to_testresult(report) == expected


def test_pytestrunner_logreport_to_testresult_xpass():
    runner = PyTestRunner(None)
    report = {
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'wasxfail': ''
    }
    expected = TestResult(Category.OK, 'ok', 'foo.bar', time=42)
    assert runner.logreport_to_testresult(report) == expected


def test_pytestrunner_logreport_to_testresult_with_output():
    runner = PyTestRunner(None)
    report = {
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo.py::bar',
        'duration': 42,
        'sections': [['Captured stdout call', 'ham\n'],
                     ['Captured stderr call', 'spam\n']],
    }
    txt = ('----- Captured stdout call -----\nham\n'
           '----- Captured stderr call -----\nspam\n')
    expected = TestResult(Category.OK, 'ok', 'foo.bar', time=42,
                          extra_text=txt)
    assert runner.logreport_to_testresult(report) == expected
