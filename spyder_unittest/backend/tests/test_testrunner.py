# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for testrunner.py"""

# Standard library imports
import os

# Local imports
from spyder_unittest.backend.testrunner import Category, TestRunner
from spyder_unittest.widgets.configdialog import Config

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


def test_testrunner_start(monkeypatch):
    MockQProcess = Mock()
    monkeypatch.setattr('spyder_unittest.backend.testrunner.QProcess',
                        MockQProcess)
    mock_process = MockQProcess()
    mock_process.systemEnvironment = lambda: ['VAR=VALUE', 'PYTHONPATH=old']

    MockEnvironment = Mock()
    monkeypatch.setattr(
        'spyder_unittest.backend.testrunner.QProcessEnvironment',
        MockEnvironment)
    mock_environment = MockEnvironment()

    mock_remove = Mock(side_effect=OSError())
    monkeypatch.setattr('spyder_unittest.backend.testrunner.os.remove',
                        mock_remove)

    runner = TestRunner(None, 'results')
    config = Config('py.test', 'wdir')
    runner.start(config, ['pythondir'])

    mock_process.setWorkingDirectory.assert_called_once_with('wdir')
    mock_process.finished.connect.assert_called_once_with(runner.finished)
    mock_process.setProcessEnvironment.assert_called_once_with(
        mock_environment)
    executable_name = 'py.test.exe' if os.name == 'nt' else 'py.test'
    mock_process.start.assert_called_once_with(executable_name,
                                               ['--junit-xml', 'results'])

    mock_environment.insert.assert_any_call('VAR', 'VALUE')
    # mock_environment.insert.assert_any_call('PYTHONPATH', 'pythondir:old')
    # TODO: Find out why above test fails
    mock_remove.called_once_with('results')


def test_testrunner_load_data(tmpdir):
    result_file = tmpdir.join('results')
    result_txt = """<?xml version="1.0" encoding="utf-8"?>
<testsuite errors="0" failures="1" name="pytest" skips="1" tests="3" time="0.1">
<testcase classname="test_foo" file="test_foo.py" line="2" name="test1" time="0.04"></testcase>
<testcase classname="test_foo" file="test_foo.py" line="5" name="test2" time="0.01">
    <failure message="failure message">text</failure>
</testcase>
<testcase classname="test_foo" file="test_foo.py" line="8" name="test3" time="0.05">
    <skipped message="skip message">text2</skipped>
</testcase></testsuite>"""
    result_file.write(result_txt)
    runner = TestRunner(None, result_file.strpath)
    results = runner.load_data()
    assert len(results) == 3

    assert results[0].category == Category.OK
    assert results[0].status == 'ok'
    assert results[0].name == 'test_foo.test1'
    assert results[0].message == ''
    assert results[0].time == 0.04
    assert results[0].extra_text == ''

    assert results[1].category == Category.FAIL
    assert results[1].status == 'failure'
    assert results[1].name == 'test_foo.test2'
    assert results[1].message == 'failure message'
    assert results[1].time == 0.01
    assert results[1].extra_text == 'text'

    assert results[2].category == Category.SKIP
    assert results[2].status == 'skipped'
    assert results[2].name == 'test_foo.test3'
    assert results[2].message == 'skip message'
    assert results[2].time == 0.05
    assert results[2].extra_text == 'text2'


def test_testrunner_load_data_failing_test_with_stdout(tmpdir):
    result_file = tmpdir.join('results')
    result_txt = """<?xml version="1.0" encoding="utf-8"?>
<testsuite errors="0" failures="1" name="pytest" skips="0" tests="1" time="0.1">
<testcase classname="test_foo" file="test_foo.py" line="2" name="test1" time="0.04">
<failure message="failure message">text</failure>
<system-out>stdout text
</system-out></testcase></testsuite>"""
    result_file.write(result_txt)
    runner = TestRunner(None, result_file.strpath)
    results = runner.load_data()
    assert results[0].extra_text == (
        'text\n\n' + '----- Captured stdout -----\n' + 'stdout text')


def test_testrunner_load_data_passing_test_with_stdout(tmpdir):
    result_file = tmpdir.join('results')
    result_txt = """<?xml version="1.0" encoding="utf-8"?>
<testsuite errors="0" failures="0" name="pytest" skips="0" tests="1" time="0.1">
<testcase classname="test_foo" file="test_foo.py" line="2" name="test1" time="0.04">
<system-out>stdout text
</system-out></testcase></testsuite>"""
    result_file.write(result_txt)
    runner = TestRunner(None, result_file.strpath)
    results = runner.load_data()
    assert results[0].extra_text == (
        '----- Captured stdout -----\n' + 'stdout text')
