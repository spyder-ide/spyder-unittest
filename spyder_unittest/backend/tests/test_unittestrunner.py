# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestrunner.py"""

# Local imports
from spyder_unittest.backend.runnerbase import Category
from spyder_unittest.backend.unittestrunner import UnittestRunner


def test_unittestrunner_load_data():
    output = """test_isupper (teststringmethods.TestStringMethods) ... ok
test_split (teststringmethods.TestStringMethods) ... ok
extra text\n"""
    runner = UnittestRunner(None)
    res = runner.load_data(output)
    assert len(res) == 2

    assert res[0].category == Category.OK
    assert res[0].status == 'ok'
    assert res[0].name == 'teststringmethods.TestStringMethods.test_isupper'
    assert res[0].message == ''
    assert res[0].extra_text == ''

    assert res[1].category == Category.OK
    assert res[1].status == 'ok'
    assert res[1].name == 'teststringmethods.TestStringMethods.test_split'
    assert res[1].message == ''
    assert res[1].extra_text == 'extra text\n'


def test_unittestrunner_removes_footer():
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
    assert res[0].message == ''
    assert res[0].extra_text == ''


def test_try_parse_header_with_ok():
    runner = UnittestRunner(None)
    text = 'test_isupper (testfoo.TestStringMethods) ... ok'
    res = runner.try_parse_result(text)
    assert res == ('test_isupper', 'testfoo.TestStringMethods', 'ok')


def test_try_parse_header_starting_with_digit():
    runner = UnittestRunner(None)
    text = '0est_isupper (testfoo.TestStringMethods) ... ok'
    res = runner.try_parse_result(text)
    assert res is None
