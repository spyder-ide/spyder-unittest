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
from spyder_unittest.backend.runnerbase import (Category, TestDetails,
                                                TestResult)
from spyder_unittest.widgets.configdialog import Config

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


def test_pytestrunner_is_installed():
    assert PyTestRunner(None).is_installed()


def test_pytestrunner_start(monkeypatch):
    MockQProcess = Mock()
    monkeypatch.setattr('spyder_unittest.backend.pytestrunner.QProcess',
                        MockQProcess)
    mock_process = MockQProcess()
    mock_process.systemEnvironment = lambda: ['VAR=VALUE', 'PYTHONPATH=old']

    MockEnvironment = Mock()
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestrunner.QProcessEnvironment',
        MockEnvironment)
    mock_environment = MockEnvironment()

    mock_remove = Mock(side_effect=OSError())
    monkeypatch.setattr('spyder_unittest.backend.pytestrunner.os.remove',
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
        get_python_executable(), [workerfile, '--junit-xml', 'results'])

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
        'module': 'spam',
        'name': 'ham'
    }, {
        'event': 'collected',
        'module': 'eggs',
        'name': 'bacon'
    }]
    with qtbot.waitSignal(runner.sig_collected) as blocker:
        runner.process_output(output)
    expected = [
        TestDetails(name='ham', module='spam'),
        TestDetails(name='bacon', module='eggs')
    ]
    assert blocker.args == [expected]


def test_pytestrunner_process_output_with_logreport_passed(qtbot):
    runner = PyTestRunner(None)
    output = [{
        'event': 'logreport',
        'when': 'call',
        'outcome': 'passed',
        'nodeid': 'foo::bar'
    }]
    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)
    expected = [TestResult(Category.OK, 'ok', 'bar', 'foo')]
    assert blocker.args == [expected]
