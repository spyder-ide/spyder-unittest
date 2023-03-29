# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for nose2runner.py"""

# Local imports
from spyder_unittest.backend.nose2runner import Nose2Runner
from spyder_unittest.backend.runnerbase import Category


def test_nose2runner_load_data(tmpdir):
    result_file = tmpdir.join('results')
    result_txt = """
<testsuite name="nose2-junit" errors="0" failures="1" skipped="0" tests="2" time="0.000">
  <testcase time="0.04" classname="test_foo" name="test1">
    <system-out />
  </testcase>
  <testcase time="0.01" classname="test_foo" name="test2">
    <failure message="test failure">text</failure>
    <system-out />
  </testcase>
</testsuite>"""
    result_file.write(result_txt)
    runner = Nose2Runner(None, result_file.strpath)
    results = runner.load_data()
    assert len(results) == 2

    assert results[0].category == Category.OK
    assert results[0].status == 'ok'
    assert results[0].name == 'test_foo.test1'
    assert results[0].message == ''
    assert results[0].time == 0.04
    assert results[0].extra_text == []

    assert results[1].category == Category.FAIL
    assert results[1].status == 'failure'
    assert results[1].name == 'test_foo.test2'
    assert results[1].message == 'test failure'
    assert results[1].time == 0.01
    assert results[1].extra_text == ['text']
