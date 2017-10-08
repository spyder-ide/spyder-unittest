# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Script for running py.test tests.

This script is meant to be run in a separate process by a PyTestRunner.
It runs tests via the py.test framework and prints the results so that the
PyTestRunner can read them.
"""

# Standard library imports
import sys

# Third party imports
import pytest


class SpyderPlugin():
    """Pytest plugin which reports in format suitable for Spyder."""

    def pytest_itemcollected(self, item):
        """Called by py.test when a test item is collected."""
        name = item.name
        module = item.parent.name
        module = module.replace('/', '.')  # convert path to dotted path
        if module.endswith('.py'):
            module = module[:-3]
        print('pytest_item_collected(name={}, module={})'.format(name, module))


pytest.main(sys.argv[1:], plugins=[SpyderPlugin()])
