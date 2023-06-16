# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for pytestworker.py"""

# Standard library imports
import os
import os.path as osp
import sys
import unittest
from unittest.mock import call, create_autospec, Mock

# Third-party imports
import pytest

# Local imports
# Modules in spyder_unittest.backend.workers assume that their directory
# is in `sys.path`, so add that directory to the path.
old_path = sys.path
sys.path.insert(0, osp.join(osp.dirname(__file__), osp.pardir))
from spyder_unittest.backend.workers.unittestworker import (
    main, report_collected, SpyderTestResult)
from spyder_unittest.backend.workers.zmqwriter import ZmqStreamWriter
sys.path = old_path


class MyTest(unittest.TestCase):
    """Simple test class."""
    def first(): pass
    def second(): pass


@pytest.fixture
def testresult():
    mock_writer = create_autospec(ZmqStreamWriter)
    my_testresult = SpyderTestResult(
            stream=Mock(), descriptions=True, verbosity=2)
    my_testresult.writer = mock_writer
    my_testresult._exc_info_to_string = lambda err, test: 'some exception info'
    return my_testresult


def test_spydertestresult_starttest(testresult):
    """Test that SpyderTestResult.startTest() writes the correct info."""
    test = MyTest(methodName='first')
    testresult.startTest(test)
    expected = {'event': 'startTest', 'id': test.id()}
    testresult.writer.write.assert_called_once_with(expected)


def test_spydertestresult_addsuccess(testresult):
    """Test that SpyderTestResult.addSuccess() writes the correct info."""
    test = MyTest(methodName='first')
    testresult.addSuccess(test)
    expected = {'event': 'addSuccess', 'id': test.id()}
    testresult.writer.write.assert_called_once_with(expected)


def test_spydertestresult_addfailure(testresult):
    """Test that SpyderTestResult.addFailure() writes the correct info."""
    test = MyTest(methodName='first')
    err = ('notused', AssertionError('xxx'), 'notused')
    testresult.addFailure(test, err)
    expected = {'event': 'addFailure',
                'id': test.id(),
                'reason': 'AssertionError: xxx',
                'err': 'some exception info'}
    testresult.writer.write.assert_called_once_with(expected)


def test_spydertestresult_adderror(testresult):
    """Test that SpyderTestResult.addError() writes the correct info."""
    test = MyTest(methodName='first')
    err = ('notused', AssertionError('xxx'), 'notused')
    testresult.addError(test, err)
    expected = {'event': 'addError',
                'id': test.id(),
                'reason': 'AssertionError: xxx',
                'err': 'some exception info'}
    testresult.writer.write.assert_called_once_with(expected)


def test_spydertestresult_addskip(testresult):
    """Test that SpyderTestResult.addSkip() writes the correct info."""
    test = MyTest(methodName='first')
    reason = 'my reason'
    testresult.addSkip(test, reason)
    expected = {'event': 'addSkip',
                'id': test.id(),
                'reason': reason}
    testresult.writer.write.assert_called_once_with(expected)


def test_spydertestresult_addexpectedfailure(testresult):
    """Test that SpyderTestResult.addExpectedFailure() writes the correct info."""
    test = MyTest(methodName='first')
    err = ('notused', AssertionError('xxx'), 'notused')
    testresult.addExpectedFailure(test, err)
    expected = {'event': 'addExpectedFailure',
                'id': test.id(),
                'reason': 'AssertionError: xxx',
                'err': 'some exception info'}
    testresult.writer.write.assert_called_once_with(expected)


def test_spydertestresult_addunexpectedsuccess(testresult):
    """Test that SpyderTestResult.addUnexpectedSuccess() writes the correct info."""
    test = MyTest(methodName='first')
    testresult.addUnexpectedSuccess(test)
    expected = {'event': 'addUnexpectedSuccess', 'id': test.id()}
    testresult.writer.write.assert_called_once_with(expected)


def test_unittestworker_report_collected():
    """
    Test that report_collected() with a test suite containing two tests
    writes two `collected` events to the ZMQ stream.
    """
    mock_writer = create_autospec(ZmqStreamWriter)
    test1 = MyTest(methodName='first')
    test2 = MyTest(methodName='second')
    test_suite_inner = unittest.TestSuite([test1, test2])
    test_suite = unittest.TestSuite([test_suite_inner])

    report_collected(mock_writer, test_suite)

    expected = [call({'event': 'collected', 'id': test1.id()}),
                call({'event': 'collected', 'id': test2.id()})]
    assert mock_writer.write.mock_calls == expected


@pytest.fixture(scope='module')
def testfile_path(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('unittestworker')
    res = tmp_path / 'test_unittestworker_foo.py'
    res.write_text('import unittest\n'
                   'class MyTest(unittest.TestCase):\n'
                   '   def test_ok(self): self.assertEqual(1+1, 2)\n'
                   '   def test_fail(self): self.assertEqual(1+1, 3)\n')
    return res


@pytest.mark.parametrize('alltests', [True, False])
def test_unittestworker_main(monkeypatch, testfile_path, alltests):
    """
    Test that the main function with some tests writes the expected
    output to the ZMQ stream.
    """
    mock_writer = create_autospec(ZmqStreamWriter)
    MockZmqStreamWriter = Mock(return_value=mock_writer)
    monkeypatch.setattr(
        'spyder_unittest.backend.workers.unittestworker.ZmqStreamWriter',
        MockZmqStreamWriter)

    os.chdir(testfile_path.parent)
    testfilename = testfile_path.stem  # `stem` removes the .py suffix
    main_args = ['mockscriptname', '42']
    if not alltests:
        main_args.append(f'{testfilename}.MyTest.test_fail')
    main(main_args)

    args = mock_writer.write.call_args_list
    messages = [arg[0][0] for arg in args]
    assert len(messages) == (6 if alltests else 3)

    assert messages[0]['event'] == 'collected'
    assert messages[0]['id'] == f'{testfilename}.MyTest.test_fail'

    if alltests:
        n = 2
        assert messages[1]['event'] == 'collected'
        assert messages[1]['id'] == f'{testfilename}.MyTest.test_ok'
    else:
        n = 1

    assert messages[n]['event'] == 'startTest'
    assert messages[n]['id'] == f'{testfilename}.MyTest.test_fail'

    assert messages[n+1]['event'] == 'addFailure'
    assert messages[n+1]['id'] == f'{testfilename}.MyTest.test_fail'
    assert 'AssertionError' in messages[n+1]['reason']
    assert 'assertEqual(1+1, 3)' in messages[n+1]['err']

    if alltests:
        assert messages[n+2]['event'] == 'startTest'
        assert messages[n+2]['id'] == f'{testfilename}.MyTest.test_ok'

        assert messages[n+3]['event'] == 'addSuccess'
        assert messages[n+3]['id'] == f'{testfilename}.MyTest.test_ok'
