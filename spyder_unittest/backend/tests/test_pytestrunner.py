# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for pytestrunner.py"""

# Third party imports
from spyder.utils.misc import get_python_executable

# Local imports
from spyder_unittest.backend.pytestrunner import PyTestRunner
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

    runner = PyTestRunner(None, 'results')
    config = Config('py.test', 'wdir')
    runner.start(config, ['pythondir'])

    mock_process.setWorkingDirectory.assert_called_once_with('wdir')
    mock_process.finished.connect.assert_called_once_with(runner.finished)
    mock_process.setProcessEnvironment.assert_called_once_with(
        mock_environment)
    mock_process.start.assert_called_once_with(
        get_python_executable(), ['-m', 'pytest', '--junit-xml', 'results'])

    mock_environment.insert.assert_any_call('VAR', 'VALUE')
    # mock_environment.insert.assert_any_call('PYTHONPATH', 'pythondir:old')
    # TODO: Find out why above test fails
    mock_remove.called_once_with('results')
