# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestgui.py."""

# Standard library imports
import os

# Third party imports
from qtpy.QtCore import Qt, QProcess
import pytest

# Local imports
from spyder_unittest.backend.runnerbase import Category, TestResult
from spyder_unittest.widgets.configdialog import Config
from spyder_unittest.widgets.unittestgui import UnitTestWidget

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock  # Python 2


def test_unittestwidget_forwards_sig_edit_goto(qtbot):
    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    with qtbot.waitSignal(widget.sig_edit_goto) as blocker:
        widget.testdataview.sig_edit_goto.emit('ham', 42)
    assert blocker.args == ['ham', 42]

def test_unittestwidget_set_config_emits_newconfig(qtbot):
    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=os.getcwd(), framework='unittest')
    with qtbot.waitSignal(widget.sig_newconfig) as blocker:
        widget.config = config
    assert blocker.args == [config]
    assert widget.config == config

def test_unittestwidget_set_config_does_not_emit_when_invalid(qtbot):
    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=os.getcwd(), framework=None)
    with qtbot.assertNotEmitted(widget.sig_newconfig):
        widget.config = config
    assert widget.config == config

def test_unittestwidget_config_with_unknown_framework_invalid(qtbot):
    """Check that if the framework in the config is not known,
    config_is_valid() returns False"""
    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=os.getcwd(), framework='unknown framework')
    assert widget.config_is_valid(config) == False

def test_unittestwidget_process_finished_updates_results(qtbot):
    widget = UnitTestWidget(None)
    widget.testdatamodel = Mock()
    widget.testdatamodel.summary = lambda: 'message'
    widget.testdatamodel.testresults = []
    results = [TestResult(Category.OK, 'ok', 'hammodule.spam')]
    widget.process_finished(results, 'output')
    assert widget.testdatamodel.testresults == results

def test_unittestwidget_process_finished_with_results_none(qtbot):
    widget = UnitTestWidget(None)
    widget.testdatamodel = Mock()
    widget.testdatamodel.summary = lambda: 'message'
    results = [TestResult(Category.OK, 'ok', 'hammodule.spam')]
    widget.testdatamodel.testresults = results
    widget.process_finished(None, 'output')
    assert widget.testdatamodel.testresults == results

def test_unittestwidget_replace_pending_with_not_run(qtbot):
    widget = UnitTestWidget(None)
    widget.testdatamodel = Mock()
    results = [TestResult(Category.PENDING, 'pending', 'hammodule.eggs'),
               TestResult(Category.OK, 'ok', 'hammodule.spam')]
    widget.testdatamodel.testresults = results
    widget.replace_pending_with_not_run()
    expected = [TestResult(Category.SKIP, 'not run', 'hammodule.eggs')]
    widget.testdatamodel.update_testresults.assert_called_once_with(expected)

def test_unittestwidget_tests_collected(qtbot):
    widget = UnitTestWidget(None)
    widget.testdatamodel = Mock()
    details = ['hammodule.spam', 'hammodule.eggs']
    widget.tests_collected(details)
    results = [TestResult(Category.PENDING, 'pending', 'hammodule.spam'),
               TestResult(Category.PENDING, 'pending', 'hammodule.eggs')]
    widget.testdatamodel.add_testresults.assert_called_once_with(results)

def test_unittestwidget_tests_started(qtbot):
    widget = UnitTestWidget(None)
    widget.testdatamodel = Mock()
    details = ['hammodule.spam']
    results = [TestResult(Category.PENDING, 'pending', 'hammodule.spam', 'running')]
    widget.tests_started(details)
    widget.testdatamodel.update_testresults.assert_called_once_with(results)

def test_unittestwidget_tests_collect_error(qtbot):
    widget = UnitTestWidget(None)
    widget.testdatamodel = Mock()
    names_plus_msg = [('hammodule.spam', 'msg')]
    results = [TestResult(Category.FAIL, 'failure', 'hammodule.spam',
                          'collection error', extra_text='msg')]
    widget.tests_collect_error(names_plus_msg)
    widget.testdatamodel.add_testresults.assert_called_once_with(results)

def test_unittestwidget_tests_yield_results(qtbot):
    widget = UnitTestWidget(None)
    widget.testdatamodel = Mock()
    results = [TestResult(Category.OK, 'ok', 'hammodule.spam')]
    widget.tests_yield_result(results)
    widget.testdatamodel.update_testresults.assert_called_once_with(results)

def test_unittestwidget_set_message(qtbot):
    widget = UnitTestWidget(None)
    widget.status_label = Mock()
    widget.set_status_label('xxx')
    widget.status_label.setText.assert_called_once_with('<b>xxx</b>')

def test_run_tests_starts_testrunner(qtbot):
    widget = UnitTestWidget(None)
    mockRunner = Mock()
    widget.framework_registry.create_runner = Mock(return_value=mockRunner)
    config = Config(wdir=None, framework='ham')
    widget.run_tests(config)
    assert widget.framework_registry.create_runner.call_count == 1
    assert widget.framework_registry.create_runner.call_args[0][0] == 'ham'
    assert mockRunner.start.call_count == 1

def test_run_tests_with_pre_test_hook_returning_true(qtbot):
    widget = UnitTestWidget(None)
    mockRunner = Mock()
    widget.framework_registry.create_runner = Mock(return_value=mockRunner)
    widget.pre_test_hook =  Mock(return_value=True)
    widget.run_tests(Config())
    assert widget.pre_test_hook.call_count == 1
    assert mockRunner.start.call_count == 1

def test_run_tests_with_pre_test_hook_returning_false(qtbot):
    widget = UnitTestWidget(None)
    mockRunner = Mock()
    widget.framework_registry.create_runner = Mock(return_value=mockRunner)
    widget.pre_test_hook =  Mock(return_value=False)
    widget.run_tests(Config())
    assert widget.pre_test_hook.call_count == 1
    assert mockRunner.start.call_count == 0

@pytest.mark.parametrize('results,label',
                         [([TestResult(Category.OK, 'ok', '')], '0 tests failed, 1 passed'),
                          ([], 'No results to show.')])
def test_unittestwidget_process_finished_updates_status_label(qtbot, results, label):
    widget = UnitTestWidget(None)
    widget.process_finished(results, 'output')
    assert widget.status_label.text() == '<b>{}</b>'.format(label)

@pytest.mark.parametrize('framework', ['pytest', 'nose'])
def test_run_tests_and_display_results(qtbot, tmpdir, monkeypatch, framework):
    """Basic integration test."""
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath

    with open(testfilename, 'w') as f:
        f.write("def test_ok(): assert 1+1 == 2\n"
                "def test_fail(): assert 1+1 == 3\n")

    MockQMessageBox = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.unittestgui.QMessageBox',
                        MockQMessageBox)

    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=tmpdir.strpath, framework=framework)
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


def test_run_tests_using_unittest_and_display_results(qtbot, tmpdir,
                                                      monkeypatch):
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

    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=tmpdir.strpath, framework='unittest')
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
def test_run_with_no_tests_discovered_and_display_results(qtbot, tmpdir,
                                                          monkeypatch, framework):
    """Basic integration test."""
    os.chdir(tmpdir.strpath)

    MockQMessageBox = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.unittestgui.QMessageBox',
                        MockQMessageBox)

    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=tmpdir.strpath, framework=framework)
    with qtbot.waitSignal(widget.sig_finished, timeout=10000, raising=True):
        widget.run_tests(config)

    MockQMessageBox.assert_not_called()
    model = widget.testdatamodel
    assert model.rowCount() == 0
    assert widget.status_label.text() == '<b>No results to show.</b>'

def test_stop_running_tests_before_testresult_is_received(qtbot, tmpdir):
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath

    with open(testfilename, 'w') as f:
        f.write("import unittest\n"
                "import time\n"
                "class MyTest(unittest.TestCase):\n"
                "   def test_ok(self): \n"
                "      time.sleep(3)\n"
                "      self.assertTrue(True)\n")

    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    config = Config(wdir=tmpdir.strpath, framework='unittest')
    widget.run_tests(config)
    qtbot.waitUntil(lambda: widget.testrunner.process.state() == QProcess.Running)
    widget.testrunner.stop_if_running()

    assert widget.testdatamodel.rowCount() == 0
    assert widget.status_label.text() == ''


def test_show_versions(monkeypatch):
    mockQMessageBox = Mock()
    monkeypatch.setattr('spyder_unittest.widgets.unittestgui.QMessageBox',
                        mockQMessageBox)
    widget = UnitTestWidget(None)
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
