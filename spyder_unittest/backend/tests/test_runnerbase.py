# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for baserunner.py"""

# Local imports
from spyder_unittest.backend.runnerbase import Category, RunnerBase


def test_runnerbase_with_nonexisting_module():
    class FooRunner(RunnerBase):
        module = 'nonexisiting'

    assert not FooRunner.is_installed()


def test_runnerbase_load_data(tmpdir):
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
    runner = RunnerBase(None, result_file.strpath)
    results = runner.load_data()
    assert len(results) == 3

    assert results[0].category == Category.OK
    assert results[0].status == 'ok'
    assert results[0].name == 'test1'
    assert results[0].module == 'test_foo'
    assert results[0].message == ''
    assert results[0].time == 0.04
    assert results[0].extra_text == ''

    assert results[1].category == Category.FAIL
    assert results[1].status == 'failure'
    assert results[1].name == 'test2'
    assert results[1].module == 'test_foo'
    assert results[1].message == 'failure message'
    assert results[1].time == 0.01
    assert results[1].extra_text == 'text'

    assert results[2].category == Category.SKIP
    assert results[2].status == 'skipped'
    assert results[2].name == 'test3'
    assert results[2].module == 'test_foo'
    assert results[2].message == 'skip message'
    assert results[2].time == 0.05
    assert results[2].extra_text == 'text2'


def test_runnerbase_load_data_failing_test_with_stdout(tmpdir):
    result_file = tmpdir.join('results')
    result_txt = """<?xml version="1.0" encoding="utf-8"?>
<testsuite errors="0" failures="1" name="pytest" skips="0" tests="1" time="0.1">
<testcase classname="test_foo" file="test_foo.py" line="2" name="test1" time="0.04">
<failure message="failure message">text</failure>
<system-out>stdout text
</system-out></testcase></testsuite>"""
    result_file.write(result_txt)
    runner = RunnerBase(None, result_file.strpath)
    results = runner.load_data()
    assert results[0].extra_text == (
        'text\n\n' + '----- Captured stdout -----\n' + 'stdout text')


def test_runnerbase_load_data_passing_test_with_stdout(tmpdir):
    result_file = tmpdir.join('results')
    result_txt = """<?xml version="1.0" encoding="utf-8"?>
<testsuite errors="0" failures="0" name="pytest" skips="0" tests="1" time="0.1">
<testcase classname="test_foo" file="test_foo.py" line="2" name="test1" time="0.04">
<system-out>stdout text
</system-out></testcase></testsuite>"""
    result_file.write(result_txt)
    runner = RunnerBase(None, result_file.strpath)
    results = runner.load_data()
    assert results[0].extra_text == (
        '----- Captured stdout -----\n' + 'stdout text')
