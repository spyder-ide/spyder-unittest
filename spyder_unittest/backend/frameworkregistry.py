# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Keep track of testing frameworks and create test runners when requested."""

# Local imports
from spyder_unittest.backend.noserunner import NoseRunner
from spyder_unittest.backend.pytestrunner import PyTestRunner


class FrameworkRegistry():
    """Registry of testing frameworks and their associated runners."""

    def create_runner(self, framework, widget, tempfilename):
        """Create test runner associated to some testing framework.

        Parameters
        ----------
        framework : str
            Name of testing framework.
        widget : UnitTestWidget
            Unit test widget which constructs the test runner.
        resultfilename : str or None
            Name of file in which to store test results. If None, use default.

        Returns
        -------
        RunnerBase
            Newly created test runner
        """
        cls = PyTestRunner if framework == 'py.test' else NoseRunner
        return cls(widget, tempfilename)
