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

pytest.main(sys.argv[1:])
