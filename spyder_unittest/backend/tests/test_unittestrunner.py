# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestrunner.py"""

# Local imports
from spyder_unittest.backend.runnerbase import Category
from spyder_unittest.backend.unittestrunner import UnittestRunner


def test_unittestrunner_load_data_with_two_tests():
    output = """test_isupper (teststringmethods.TestStringMethods) ... ok
test_split (teststringmethods.TestStringMethods) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.012s

OK
"""
    runner = UnittestRunner(None)
    res = runner.load_data(output)
    assert len(res) == 2

    assert res[0].category == Category.OK
    assert res[0].status == 'ok'
    assert res[0].name == 'teststringmethods.TestStringMethods.test_isupper'
    assert res[0].message == ''
    assert res[0].extra_text == []

    assert res[1].category == Category.OK
    assert res[1].status == 'ok'
    assert res[1].name == 'teststringmethods.TestStringMethods.test_split'
    assert res[1].message == ''
    assert res[1].extra_text == []


def test_unittestrunner_load_data_with_one_test():
    output = """test1 (test_foo.Bar) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
"""
    runner = UnittestRunner(None)
    res = runner.load_data(output)
    assert len(res) == 1
    assert res[0].category == Category.OK
    assert res[0].status == 'ok'
    assert res[0].name == 'test_foo.Bar.test1'
    assert res[0].extra_text == []


def test_unittestrunner_load_data_with_exception():
    output = """test1 (test_foo.Bar) ... FAIL
test2 (test_foo.Bar) ... ok

======================================================================
FAIL: test1 (test_foo.Bar)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/somepath/test_foo.py", line 5, in test1
    self.assertEqual(1, 2)
AssertionError: 1 != 2

----------------------------------------------------------------------
Ran 2 tests in 0.012s

FAILED (failures=1)
"""
    runner = UnittestRunner(None)
    res = runner.load_data(output)
    assert len(res) == 2

    assert res[0].category == Category.FAIL
    assert res[0].status == 'FAIL'
    assert res[0].name == 'test_foo.Bar.test1'
    assert res[0].extra_text[0].startswith('Traceback')
    assert res[0].extra_text[-1].endswith('AssertionError: 1 != 2')

    assert res[1].category == Category.OK
    assert res[1].status == 'ok'
    assert res[1].name == 'test_foo.Bar.test2'
    assert res[1].extra_text == []


def test_unittestrunner_load_data_with_comment():
    output = """test1 (test_foo.Bar)
comment ... ok
test2 (test_foo.Bar) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK
"""
    runner = UnittestRunner(None)
    res = runner.load_data(output)
    assert len(res) == 2

    assert res[0].category == Category.OK
    assert res[0].status == 'ok'
    assert res[0].name == 'test_foo.Bar.test1'
    assert res[0].extra_text == []

    assert res[1].category == Category.OK
    assert res[1].status == 'ok'
    assert res[1].name == 'test_foo.Bar.test2'
    assert res[1].extra_text == []


def test_unittestrunner_load_data_with_fail_and_comment():
    output = """test1 (test_foo.Bar)
comment ... FAIL

======================================================================
FAIL: test1 (test_foo.Bar)
comment
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/somepath/test_foo.py", line 30, in test1
    self.assertEqual(1, 2)
AssertionError: 1 != 2

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
"""
    runner = UnittestRunner(None)
    res = runner.load_data(output)
    assert len(res) == 1

    assert res[0].category == Category.FAIL
    assert res[0].status == 'FAIL'
    assert res[0].name == 'test_foo.Bar.test1'
    assert res[0].extra_text[0].startswith('Traceback')
    assert res[0].extra_text[-1].endswith('AssertionError: 1 != 2')


def test_try_parse_header_with_ok():
    runner = UnittestRunner(None)
    lines = ['test_isupper (testfoo.TestStringMethods) ... ok']
    res = runner.try_parse_result(lines, 0)
    assert res == (1, 'test_isupper', 'testfoo.TestStringMethods', 'ok', '')


def test_try_parse_header_with_xfail():
    runner = UnittestRunner(None)
    lines = ['test_isupper (testfoo.TestStringMethods) ... expected failure']
    res = runner.try_parse_result(lines, 0)
    assert res == (1, 'test_isupper', 'testfoo.TestStringMethods',
                   'expected failure', '')


def test_try_parse_header_with_message():
    runner = UnittestRunner(None)
    lines = ["test_nothing (testfoo.Tests) ... skipped 'msg'"]
    res = runner.try_parse_result(lines, 0)
    assert res == (1, 'test_nothing', 'testfoo.Tests', 'skipped', 'msg')


def test_try_parse_header_starting_with_digit():
    runner = UnittestRunner(None)
    lines = ['0est_isupper (testfoo.TestStringMethods) ... ok']
    res = runner.try_parse_result(lines, 0)
    assert res is None


def test_get_versions(monkeypatch):
    import platform
    monkeypatch.setattr(platform, 'python_version', lambda: '1.2.3')
    runner = UnittestRunner(None)
    assert runner.get_versions() == ['unittest 1.2.3']
