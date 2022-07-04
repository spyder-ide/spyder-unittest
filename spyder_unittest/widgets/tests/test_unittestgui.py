# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestgui.py."""

# Standard library imports
import os
import sys
from unittest.mock import Mock

# Third party imports
from qtpy.QtCore import Qt, QProcess
import pytest

# Local imports
from spyder_unittest.backend.runnerbase import (Category, TestResult,
                                                COV_TEST_NAME)
from spyder_unittest.widgets.configdialog import Config
from spyder_unittest.widgets.unittestgui import UnitTestWidget


@pytest.fixture
def widget(qtbot):
    unittest_widget = UnitTestWidget('testwidget', None, None)
    unittest_widget.get_conf(
        'executable',
        section='main_interpreter',
        default=sys.executable)
    unittest_widget.setup()
    qtbot.addWidget(unittest_widget)
    return unittest_widget

def use_mock_model(widget):
    """Replace data model in unit test widget with mock model."""
    widget.testdatamodel = Mock()
    widget.testdatamodel.summary = lambda: 'message'
    widget.testdatamodel.testresults = []

def test_unittestwidget_forwards_sig_edit_goto(qtbot, widget):
    with qtbot.waitSignal(widget.sig_edit_goto) as blocker:
        widget.testdataview.sig_edit_goto.emit('ham', 42)
    assert blocker.args == ['ham', 42]

def test_unittestwidget_set_config_emits_newconfig(qtbot, widget):
    config = Config(wdir=os.getcwd(), framework='unittest', coverage=False)
    with qtbot.waitSignal(widget.sig_newconfig) as blocker:
        widget.config = config
    assert blocker.args == [config]
    assert widget.config == config

def test_unittestwidget_set_config_does_not_emit_when_invalid(qtbot, widget):
    config = Config(wdir=os.getcwd(), framework=None, coverage=False)
    with qtbot.assertNotEmitted(widget.sig_newconfig):
        widget.config = config
    assert widget.config == config

def test_unittestwidget_config_with_unknown_framework_invalid(widget):
    """Check that if the framework in the config is not known,
    config_is_valid() returns False"""
    config = Config(
        wdir=os.getcwd(), framework='unknown framework', coverage=False)
    assert widget.config_is_valid(config) == False

def test_unittestwidget_process_finished_updates_results(widget):
    results = [TestResult(Category.OK, 'ok', 'hammodule.spam')]
    widget.process_finished(results, 'output')
    assert widget.testdatamodel.testresults == results

def test_unittestwidget_replace_pending_with_not_run(widget):
    use_mock_model(widget)
    results = [TestResult(Category.PENDING, 'pending', 'hammodule.eggs'),
               TestResult(Category.OK, 'ok', 'hammodule.spam')]
    widget.testdatamodel.testresults = results
    widget.replace_pending_with_not_run()
    expected = [TestResult(Category.SKIP, 'not run', 'hammodule.eggs')]
    widget.testdatamodel.update_testresults.assert_called_once_with(expected)

def test_unittestwidget_tests_collected(widget):
    use_mock_model(widget)
    details = ['hammodule.spam', 'hammodule.eggs']
    widget.tests_collected(details)
    results = [TestResult(Category.PENDING, 'pending', 'hammodule.spam'),
               TestResult(Category.PENDING, 'pending', 'hammodule.eggs')]
    widget.testdatamodel.add_testresults.assert_called_once_with(results)

def test_unittestwidget_tests_started(widget):
    use_mock_model(widget)
    details = ['hammodule.spam']
    results = [TestResult(Category.PENDING, 'pending', 'hammodule.spam', 'running')]
    widget.tests_started(details)
    widget.testdatamodel.update_testresults.assert_called_once_with(results)

def test_unittestwidget_tests_collect_error(widget):
    use_mock_model(widget)
    names_plus_msg = [('hammodule.spam', 'msg')]
    results = [TestResult(Category.FAIL, 'failure', 'hammodule.spam',
                          'collection error', extra_text='msg')]
    widget.tests_collect_error(names_plus_msg)
    widget.testdatamodel.add_testresults.assert_called_once_with(results)

def test_unittestwidget_tests_yield_results(widget):
    use_mock_model(widget)
    results = [TestResult(Category.OK, 'ok', 'hammodule.spam')]
    widget.tests_yield_result(results)
    widget.testdatamodel.update_testresults.assert_called_once_with(results)

def test_unittestwidget_set_message(widget):
    widget.status_label = Mock()
    widget.set_status_label('xxx')
    widget.status_label.setText.assert_called_once_with('<b>xxx</b>')

def test_run_tests_starts_testrunner(widget):
    mockRunner = Mock()
    widget.framework_registry.create_runner = Mock(return_value=mockRunner)
    config = Config(wdir=None, framework='ham', coverage=False)
    widget.run_tests(config)
    assert widget.framework_registry.create_runner.call_count == 1
    assert widget.framework_registry.create_runner.call_args[0][0] == 'ham'
    assert mockRunner.start.call_count == 1

def test_run_tests_with_pre_test_hook_returning_true(widget):
    mockRunner = Mock()
    widget.framework_registry.create_runner = Mock(return_value=mockRunner)
    widget.pre_test_hook = Mock(return_value=True)
    widget.run_tests(Config())
    assert widget.pre_test_hook.call_count == 1
    assert mockRunner.start.call_count == 1

def test_run_tests_with_pre_test_hook_returning_false(widget):
    mockRunner = Mock()
    widget.framework_registry.create_runner = Mock(return_value=mockRunner)
    widget.pre_test_hook =  Mock(return_value=False)
    widget.run_tests(Config())
    assert widget.pre_test_hook.call_count == 1
    assert mockRunner.start.call_count == 0

@pytest.mark.parametrize('results,label',
                         [([TestResult(Category.OK, 'ok', '')], '0 tests failed, 1 passed'),
                          ([], 'No results to show.'),
                          ([TestResult(Category.OK, 'ok', ''),
                           TestResult(Category.COVERAGE, '90%', COV_TEST_NAME)],
                          '0 tests failed, 1 passed, 90% coverage')])
def test_unittestwidget_process_finished_updates_status_label(widget, results, label):
    widget.process_finished(results, 'output')
    assert widget.status_label.text() == '<b>{}</b>'.format(label)

@pytest.mark.parametrize('framework', ['pytest', 'nose'])
def test_run_tests_and_display_results(qtbot, widget, tmpdir, monkeypatch, framework):
    """Basic integration test."""
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath

    with open(testfilename, 'w') as f:
        f.write("def test_ok(): assert 1+1 == 2\n"
                "def test_fail(): assert 1+1 == 3\n")

    MockQMessageBox = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.unittestgui.QMessageBox',
                        MockQMessageBox)

    config = Config(wdir=tmpdir.strpath, framework=framework, coverage=False)
    with qtbot.waitSignal(widget.sig_finished, timeout=10000, raising=True):
        widget.run_tests(config)

    MockQMessageBox.assert_not_called()
    model = widget.testdatamodel
    assert model.rowCount() == 2
    assert model.index(0, 0).data(
        Qt.DisplayRole) == 'ok' if framework == 'nose' else 'passed'
    assert model.index(0, 1).data(Qt.DisplayRole) == 't.test_ok'
    assert model.index(0, 1).data(Qt.ToolTipRole) == 'test_foo.test_ok'
    assert model.index(0, 2).data(Qt.DisplayRole) == ''
    assert model.index(1, 0).data(
        Qt.DisplayRole) == 'failure' if framework == 'nose' else 'failed'
    assert model.index(1, 1).data(Qt.DisplayRole) == 't.test_fail'
    assert model.index(1, 1).data(Qt.ToolTipRole) == 'test_foo.test_fail'


def test_run_tests_using_unittest_and_display_results(
        qtbot, widget, tmpdir, monkeypatch):
    """Basic check."""
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath

    with open(testfilename, 'w') as f:
        f.write("import unittest\n"
                "class MyTest(unittest.TestCase):\n"
                "   def test_ok(self): self.assertEqual(1+1, 2)\n"
                "   def test_fail(self): self.assertEqual(1+1, 3)\n")

    MockQMessageBox = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.unittestgui.QMessageBox',
                        MockQMessageBox)

    config = Config(wdir=tmpdir.strpath, framework='unittest', coverage=False)
    with qtbot.waitSignal(widget.sig_finished, timeout=10000, raising=True):
        widget.run_tests(config)

    MockQMessageBox.assert_not_called()
    model = widget.testdatamodel
    assert model.rowCount() == 2
    assert model.index(0, 0).data(Qt.DisplayRole) == 'FAIL'
    assert model.index(0, 1).data(Qt.DisplayRole) == 't.M.test_fail'
    assert model.index(0, 1).data(Qt.ToolTipRole) == 'test_foo.MyTest.test_fail'
    assert model.index(0, 2).data(Qt.DisplayRole) == ''
    assert model.index(1, 0).data(Qt.DisplayRole) == 'ok'
    assert model.index(1, 1).data(Qt.DisplayRole) == 't.M.test_ok'
    assert model.index(1, 1).data(Qt.ToolTipRole) == 'test_foo.MyTest.test_ok'
    assert model.index(1, 2).data(Qt.DisplayRole) == ''

@pytest.mark.parametrize('framework', ['unittest', 'pytest', 'nose'])
def test_run_with_no_tests_discovered_and_display_results(
        qtbot, widget, tmpdir, monkeypatch, framework):
    """Basic integration test."""
    os.chdir(tmpdir.strpath)

    MockQMessageBox = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.unittestgui.QMessageBox',
                        MockQMessageBox)

    config = Config(wdir=tmpdir.strpath, framework=framework, coverage=False)
    with qtbot.waitSignal(widget.sig_finished, timeout=10000, raising=True):
        widget.run_tests(config)

    MockQMessageBox.assert_not_called()
    model = widget.testdatamodel
    assert model.rowCount() == 0
    assert widget.status_label.text() == '<b>No results to show.</b>'

def test_stop_running_tests_before_testresult_is_received(qtbot, widget, tmpdir):
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath

    with open(testfilename, 'w') as f:
        f.write("import unittest\n"
                "import time\n"
                "class MyTest(unittest.TestCase):\n"
                "   def test_ok(self): \n"
                "      time.sleep(3)\n"
                "      self.assertTrue(True)\n")

    config = Config(wdir=tmpdir.strpath, framework='unittest', coverage=False)
    widget.run_tests(config)
    qtbot.waitUntil(lambda: widget.testrunner.process.state() == QProcess.Running)
    widget.testrunner.stop_if_running()

    assert widget.testdatamodel.rowCount() == 0
    assert widget.status_label.text() == ''


def test_show_versions(monkeypatch, widget):
    mockQMessageBox = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.unittestgui.QMessageBox',
                        mockQMessageBox)
    monkeypatch.setattr(widget.framework_registry.frameworks['nose'],
                        'is_installed', lambda: False)
    monkeypatch.setattr(widget.framework_registry.frameworks['pytest'],
                        'is_installed', lambda: True)
    monkeypatch.setattr(widget.framework_registry.frameworks['unittest'],
                        'is_installed', lambda: True)
    monkeypatch.setattr(widget.framework_registry.frameworks['nose'],
                        'get_versions', lambda _: [])
    monkeypatch.setattr(widget.framework_registry.frameworks['pytest'],
                        'get_versions',
                        lambda _: ['pytest 1.2.3', '   plugin1 4.5.6',
                                   '   plugin2 7.8.9'])
    monkeypatch.setattr(widget.framework_registry.frameworks['unittest'],
                        'get_versions', lambda _: ['unittest 1.2.3'])
    widget.show_versions()
    expected = ('Versions of frameworks and their installed plugins:\n\n'
                'nose: not available\n\npytest 1.2.3\n   plugin1 4.5.6\n   '
                'plugin2 7.8.9\n\nunittest 1.2.3')
    mockQMessageBox.information.assert_called_with(widget, 'Dependencies',
                                                   expected)
