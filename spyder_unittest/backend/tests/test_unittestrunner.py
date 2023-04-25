# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestrunner.py"""

# Standard library imports
import os.path as osp
import sys
from unittest.mock import Mock

# Local imports
from spyder_unittest.backend.unittestrunner import UnittestRunner
from spyder_unittest.backend.runnerbase import Category, TestResult
from spyder_unittest.widgets.configdialog import Config


def test_unittestrunner_create_argument_list(monkeypatch):
    """
    Test that UnittestRunner.createArgumentList() returns the expected list.
    """
    config = Config()
    cov_path = None
    MockZMQStreamReader = Mock()
    monkeypatch.setattr(
        'spyder_unittest.backend.unittestrunner.ZmqStreamReader',
        MockZMQStreamReader)
    mock_reader = MockZMQStreamReader()
    mock_reader.port = 42
    runner = UnittestRunner(None, 'resultfile')
    runner.reader = mock_reader
    monkeypatch.setattr(
        'spyder_unittest.backend.unittestrunner.osp.dirname',
        lambda _: 'dir')

    result = runner.create_argument_list(config, cov_path)

    pyfile = osp.join('dir', 'workers', 'unittestworker.py')
    assert result == [pyfile, '42']


def test_unittestrunner_start(monkeypatch):
    """
    Test that UnittestRunner.start() sets the .config and .reader members
    correctly, that it connects to the reader's sig_received, and that it
    called the base class method.
    """
    MockZMQStreamReader = Mock()
    monkeypatch.setattr(
        'spyder_unittest.backend.unittestrunner.ZmqStreamReader',
        MockZMQStreamReader)
    mock_reader = MockZMQStreamReader()
    mock_base_start = Mock()
    monkeypatch.setattr('spyder_unittest.backend.unittestrunner.RunnerBase.start',
                        mock_base_start)
    runner = UnittestRunner(None, 'results')
    config = Config()
    cov_path = None

    runner.start(config, cov_path, sys.executable, ['pythondir'])

    assert runner.config is config
    assert runner.reader is mock_reader
    runner.reader.sig_received.connect.assert_called_once_with(
        runner.process_output)
    mock_base_start.assert_called_once_with(
        config, cov_path, sys.executable, ['pythondir'])


def test_unittestrunner_process_output_with_collected(qtbot):
    """Test UnittestRunner.processOutput() with two `collected` events."""
    runner = UnittestRunner(None)
    output = [{'event': 'collected', 'id': 'spam.ham'},
              {'event': 'collected', 'id': 'eggs.bacon'}]

    with qtbot.waitSignal(runner.sig_collected) as blocker:
        runner.process_output(output)

    expected = ['spam.ham', 'eggs.bacon']
    assert blocker.args == [expected]


def test_unittestrunner_process_output_with_starttest(qtbot):
    """Test UnittestRunner.processOutput() with two `startTest` events."""
    runner = UnittestRunner(None)
    output = [{'event': 'startTest', 'id': 'spam.ham'},
              {'event': 'startTest', 'id': 'eggs.bacon'}]

    with qtbot.waitSignal(runner.sig_starttest) as blocker:
        runner.process_output(output)

    expected = ['spam.ham', 'eggs.bacon']
    assert blocker.args == [expected]


def test_unittestrunner_process_output_with_addsuccess(qtbot):
    """Test UnittestRunner.processOutput() with an `addSuccess` event."""
    runner = UnittestRunner(None)
    output = [{'event': 'addSuccess', 'id': 'spam.ham'}]

    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)

    expected = [TestResult(Category.OK, 'success', 'spam.ham')]
    assert blocker.args == [expected]


def test_unittestrunner_process_output_with_addfailure(qtbot):
    """Test UnittestRunner.processOutput() with an `addFailure` event."""
    runner = UnittestRunner(None)
    output = [{'event': 'addFailure',
               'id': 'spam.ham',
               'reason': 'exception',
               'err': 'traceback'}]

    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)

    expected = [TestResult(Category.FAIL, 'failure', 'spam.ham',
                           message='exception', extra_text='traceback')]
    assert blocker.args == [expected]


def test_unittestrunner_process_output_with_adderror(qtbot):
    """Test UnittestRunner.processOutput() with an `addError` event."""
    runner = UnittestRunner(None)
    output = [{'event': 'addError',
               'id': 'spam.ham',
               'reason': 'exception',
               'err': 'traceback'}]

    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)

    expected = [TestResult(Category.FAIL, 'error', 'spam.ham',
                           message='exception', extra_text='traceback')]
    assert blocker.args == [expected]


def test_unittestrunner_process_output_with_addskip(qtbot):
    """Test UnittestRunner.processOutput() with an `addSkip` event."""
    runner = UnittestRunner(None)
    output = [{'event': 'addSkip',
               'id': 'spam.ham',
               'reason': 'skip reason'}]

    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)

    expected = [TestResult(Category.SKIP, 'skip', 'spam.ham',
                           message='skip reason')]
    assert blocker.args == [expected]


def test_unittestrunner_process_output_with_addexpectedfailure(qtbot):
    """Test UnittestRunner.processOutput() with an `addExpectedFailure` event."""
    runner = UnittestRunner(None)
    output = [{'event': 'addExpectedFailure',
               'id': 'spam.ham',
               'reason': 'exception',
               'err': 'traceback'}]

    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)

    expected = [TestResult(Category.OK, 'expectedFailure', 'spam.ham',
                           message='exception', extra_text='traceback')]
    assert blocker.args == [expected]


def test_unittestrunner_process_output_with_addunexpectedsuccess(qtbot):
    """Test UnittestRunner.processOutput() with an `addUnexpectedSuccess` event."""
    runner = UnittestRunner(None)
    output = [{'event': 'addUnexpectedSuccess', 'id': 'spam.ham'}]

    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)

    expected = [TestResult(Category.FAIL, 'unexpectedSuccess', 'spam.ham')]
    assert blocker.args == [expected]
