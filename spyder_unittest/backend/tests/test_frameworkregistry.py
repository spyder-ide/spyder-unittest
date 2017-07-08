# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for frameworkregistry.py"""

# Third party imports
import pytest

# Local imports
from spyder_unittest.backend.frameworkregistry import FrameworkRegistry


class MockRunner:
    name = 'foo'

    def __init__(self, *args):
        self.init_args = args


def test_frameworkregistry_when_empty():
    reg = FrameworkRegistry()
    with pytest.raises(KeyError):
        reg.create_runner('foo', None, 'temp.txt')


def test_frameworkregistry_after_registering():
    reg = FrameworkRegistry()
    reg.register(MockRunner)
    runner = reg.create_runner('foo', None, 'temp.txt')
    assert isinstance(runner, MockRunner)
    assert runner.init_args == (None, 'temp.txt')
