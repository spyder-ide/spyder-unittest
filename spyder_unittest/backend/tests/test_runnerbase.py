# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for baserunner.py"""

# Local imports
from spyder_unittest.backend.runnerbase import RunnerBase


def test_runnerbase_with_nonexisting_module():
    class FooRunner(RunnerBase):
        module = 'nonexisiting'

    assert not FooRunner.is_installed()
