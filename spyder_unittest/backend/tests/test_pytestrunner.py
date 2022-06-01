# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for pytestrunner.py"""

# Standard library imports
import os
import os.path as osp
import sys

# Third party imports
import pytest

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
    runner.start(config, sys.executable, ['pythondir'])
    assert runner.config is config
    assert runner.reader is mock_reader
    runner.reader.sig_received.connect.assert_called_once_with(
        runner.process_output)
    MockRunnerBase.start.assert_called_once_with(
        runner, config, sys.executable, ['pythondir'])


@pytest.mark.skip("segfaulting for some reason")
def test_pytestrunner_process_output_with_collected(qtbot):
    runner = PyTestRunner(None)
    output = [{'event': 'collected', 'nodeid': 'spam.py::ham'},
              {'event': 'collected', 'nodeid': 'eggs.py::bacon'}]
    with qtbot.waitSignal(runner.sig_collected) as blocker:
        runner.process_output(output)
    expected = ['spam.ham', 'eggs.bacon']
    assert blocker.args == [expected]


@pytest.mark.skip("segfaulting for some reason")
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


@pytest.mark.skip("segfaulting for some reason")
def test_pytestrunner_process_output_with_starttest(qtbot):
    runner = PyTestRunner(None)
    output = [{'event': 'starttest', 'nodeid': 'ham/spam.py::ham'},
              {'event': 'starttest', 'nodeid': 'ham/eggs.py::bacon'}]
    with qtbot.waitSignal(runner.sig_starttest) as blocker:
        runner.process_output(output)
    expected = ['ham.spam.ham', 'ham.eggs.bacon']
    assert blocker.args == [expected]


@pytest.mark.parametrize('output,results', [
    ('== 1 passed in 0.10s ==', None),
    ('== no tests ran 0.01s ==', [])
])
def test_pytestrunner_finished(qtbot, output, results):
    mock_reader = Mock()
    mock_reader.close = lambda: None
    runner = PyTestRunner(None)
    runner.reader = mock_reader
    runner.read_all_process_output = lambda: output
    with qtbot.waitSignal(runner.sig_finished) as blocker:
        runner.finished()
    assert blocker.args == [results, output]


def standard_logreport_output():
    return {
        'event': 'logreport',
        'outcome': 'passed',
        'witherror': False,
        'nodeid': 'foo.py::bar',
        'filename': 'foo.py',
        'lineno': 24,
        'duration': 42
    }

def test_pytestrunner_process_output_with_logreport_passed(qtbot):
    runner = PyTestRunner(None)
    runner.rootdir = 'ham'
    output = [standard_logreport_output()]
    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_output(output)
    expected = [TestResult(Category.OK, 'passed', 'foo.bar', time=42,
                           filename=osp.join('ham', 'foo.py'), lineno=24)]
    assert blocker.args == [expected]


@pytest.mark.parametrize('outcome,witherror,category', [
    ('passed', True, Category.FAIL),
    ('passed', False, Category.OK),
    ('failed', True, Category.FAIL),
    ('failed', False, Category.FAIL),
    # ('skipped', True, this is not possible)
    ('skipped', False, Category.SKIP),
    ('xfailed', True, Category.FAIL),
    ('xfailed', False, Category.OK),
    ('xpassed', True, Category.FAIL),
    ('xpassed', False, Category.FAIL),
    ('---', True, Category.FAIL)
    # ('---', False, this is not possible)
])
def test_logreport_to_testresult_with_outcome_and_possible_error(outcome,
                                                                 witherror,
                                                                 category):
    report = standard_logreport_output()
    report['outcome'] = outcome
    report['witherror'] = witherror
    expected = TestResult(category, outcome, 'foo.bar', time=42,
                          filename=osp.join('ham', 'foo.py'), lineno=24)
    assert logreport_to_testresult(report, 'ham') == expected


def test_logreport_to_testresult_with_message():
    report = standard_logreport_output()
    report['message'] = 'msg'
    expected = TestResult(Category.OK, 'passed', 'foo.bar', message='msg',
                          time=42, filename=osp.join('ham', 'foo.py'),
                          lineno=24)
    assert logreport_to_testresult(report, 'ham') == expected


def test_logreport_to_testresult_with_extratext():
    report = standard_logreport_output()
    report['longrepr'] = 'long msg'
    expected = TestResult(Category.OK, 'passed', 'foo.bar', time=42,
                          extra_text='long msg',
                          filename=osp.join('ham', 'foo.py'), lineno=24)
    assert logreport_to_testresult(report, 'ham') == expected


@pytest.mark.parametrize('longrepr,prefix', [
    ('', ''),
    ('msg', '\n')
])
def test_logreport_to_testresult_with_output(longrepr, prefix):
    report = standard_logreport_output()
    report['longrepr'] = longrepr
    report['sections'] = [['Captured stdout call', 'ham\n'],
                          ['Captured stderr call', 'spam\n']]
    txt = (longrepr + prefix +
           '----- Captured stdout call -----\nham\n'
           '----- Captured stderr call -----\nspam\n')
    expected = TestResult(Category.OK, 'passed', 'foo.bar', time=42,
                          extra_text=txt, filename=osp.join('ham', 'foo.py'),
                          lineno=24)
    assert logreport_to_testresult(report, 'ham') == expected


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
