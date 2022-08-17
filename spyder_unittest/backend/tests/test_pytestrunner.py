# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for pytestrunner.py"""

# Standard library imports
import os.path as osp
import sys
from unittest.mock import Mock

# Third party imports
import pytest

# Local imports
from spyder_unittest.backend.pytestrunner import (PyTestRunner,
                                                  logreport_to_testresult)
from spyder_unittest.backend.runnerbase import (Category, TestResult,
                                                COV_TEST_NAME)
from spyder_unittest.widgets.configdialog import Config


def test_pytestrunner_create_argument_list(monkeypatch):
    config = Config()
    cov_path = None
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
    pyfile, port, *coverage = runner.create_argument_list(config, cov_path)
    assert pyfile == osp.join('dir', 'workers', 'pytestworker.py')
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
    cov_path = None
    runner.start(config, cov_path, sys.executable, ['pythondir'])
    assert runner.config is config
    assert runner.reader is mock_reader
    runner.reader.sig_received.connect.assert_called_once_with(
        runner.process_output)
    MockRunnerBase.start.assert_called_once_with(
        runner, config, cov_path, sys.executable, ['pythondir'])


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


@pytest.mark.parametrize('exitcode, normal_exit', 
                         [(0, True), (1, True), (2, True), (3, False),
                          (4, False), (5, True)])
def test_pytestrunner_finished(qtbot, exitcode, normal_exit):
    output = '== 1 passed in 0.10s =='
    mock_reader = Mock()
    mock_reader.close = lambda: None
    runner = PyTestRunner(None)
    runner.reader = mock_reader
    runner.read_all_process_output = lambda: output
    runner.config = Config('pytest', None, False)
    with qtbot.waitSignal(runner.sig_finished) as blocker:
        runner.finished(exitcode)
    results = []
    assert blocker.args == [results, output, normal_exit]


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


def test_pytestrunner_process_coverage(qtbot):
    output = """
============================= test session starts ==============================
platform linux -- Python 3.9.12, pytest-7.1.2, pluggy-1.0.0
PyQt5 5.12.3 -- Qt runtime 5.12.9 -- Qt compiled 5.12.9
rootdir: /TRAC/TRAC-data/spyder-unittest, configfile: setup.cfg
plugins: flaky-3.7.0, cov-3.0.0, qt-4.0.2, mock-3.7.0
collected 152 items

spyder_unittest/backend/tests/test_abbreviator.py ...........            [  7%]
spyder_unittest/backend/tests/test_frameworkregistry.py ..               [  8%]
spyder_unittest/backend/tests/test_noserunner.py .....                   [ 11%]
spyder_unittest/backend/tests/test_pytestrunner.py ..................... [ 25%]
....                                                                     [ 28%]
spyder_unittest/backend/tests/test_pytestworker.py ..................... [ 42%]
....                                                                     [ 44%]
spyder_unittest/backend/tests/test_runnerbase.py .....                   [ 48%]
spyder_unittest/backend/tests/test_unittestrunner.py ..........          [ 54%]
spyder_unittest/backend/tests/test_zmqstream.py .                        [ 55%]
spyder_unittest/tests/test_unittestplugin.py s.sss                       [ 58%]
spyder_unittest/widgets/tests/test_configdialog.py ...........           [ 65%]
spyder_unittest/widgets/tests/test_datatree.py ......................... [ 82%]
..                                                                       [ 83%]
spyder_unittest/widgets/tests/test_unittestgui.py ...................... [ 98%]
...                                                                      [100%]

=============================== warnings summary ===============================

---------- coverage: platform linux, python 3.9.12-final-0 -----------
Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
setup.py                                       26     26     0%   7-53
spyder_unittest/backend/noserunner.py          62      7    89%   17-19, 71-72, 94, 103
spyder_unittest/backend/pytestrunner.py       101      6    94%   100-106
spyder_unittest/backend/pytestworker.py        78      4    95%   36, 40, 44, 152
spyder_unittest/backend/runnerbase.py          87      2    98%   20-21
spyder_unittest/backend/unittestrunner.py      78      5    94%   69, 75, 123, 138, 146
spyder_unittest/unittestplugin.py             119     65    45%   60, 71, 119-123, 136-141, 148-150, 161, 170-173, 183-186, 207-208, 219-226, 240-272, 280-289, 299-301, 313-314
spyder_unittest/widgets/configdialog.py        95     10    89%   28-30, 134-135, 144, 173-176
spyder_unittest/widgets/datatree.py           244     14    94%   26-28, 100, 105, 107, 276-277, 280, 293, 312, 417, 422-424
spyder_unittest/widgets/unittestgui.py        218     35    84%   41-43, 49, 223, 241, 245, 249-256, 271-278, 302-305, 330, 351-352, 468-482
-------------------------------------------------------------------------
TOTAL                                        1201    174    86%

6 files skipped due to complete coverage.

================= 148 passed, 4 skipped, 242 warnings in 4.25s =================
    """
    cov_text = """
---------- coverage: platform linux, python 3.9.12-final-0 -----------
Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
setup.py                                       26     26     0%   7-53
spyder_unittest/backend/noserunner.py          62      7    89%   17-19, 71-72, 94, 103
spyder_unittest/backend/pytestrunner.py       101      6    94%   100-106
spyder_unittest/backend/pytestworker.py        78      4    95%   36, 40, 44, 152
spyder_unittest/backend/runnerbase.py          87      2    98%   20-21
spyder_unittest/backend/unittestrunner.py      78      5    94%   69, 75, 123, 138, 146
spyder_unittest/unittestplugin.py             119     65    45%   60, 71, 119-123, 136-141, 148-150, 161, 170-173, 183-186, 207-208, 219-226, 240-272, 280-289, 299-301, 313-314
spyder_unittest/widgets/configdialog.py        95     10    89%   28-30, 134-135, 144, 173-176
spyder_unittest/widgets/datatree.py           244     14    94%   26-28, 100, 105, 107, 276-277, 280, 293, 312, 417, 422-424
spyder_unittest/widgets/unittestgui.py        218     35    84%   41-43, 49, 223, 241, 245, 249-256, 271-278, 302-305, 330, 351-352, 468-482
-------------------------------------------------------------------------
TOTAL                                        1201    174    86%

6 files skipped due to complete coverage."""
    runner = PyTestRunner(None)
    runner.rootdir = 'ham'
    with qtbot.waitSignal(runner.sig_testresult) as blocker:
        runner.process_coverage(output)
    expected = TestResult(
        Category.COVERAGE, "86%", COV_TEST_NAME, extra_text=cov_text)


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

