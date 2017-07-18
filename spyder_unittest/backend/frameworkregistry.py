# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Keep track of testing frameworks and create test runners when requested."""


class FrameworkRegistry():
    """
    Registry of testing frameworks and their associated runners.

    The test runner for a framework is responsible for running the tests and
    parsing the results. It should implement the interface of RunnerBase.

    Frameworks should first be registered using `.register()`. This registry
    can then create the assoicated test runner when `.create_runner()` is
    called.

    Attributes
    ----------
    frameworks : dict of (str, type)
        Dictionary mapping names of testing frameworks to the types of the
        associated runners.
    """

    def __init__(self):
        """Initialize self."""
        self.frameworks = {}

    def register(self, runner_class):
        """Register runner class for a testing framework.

        Parameters
        ----------
        runner_class : type
            Class used for creating tests runners for the framework.
        """
        self.frameworks[runner_class.name] = runner_class

    def create_runner(self, framework, widget, tempfilename):
        """Create test runner associated to some testing framework.

        This creates an instance of the runner class whose `name` attribute
        equals `framework`.

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

        Exceptions
        ----------
        KeyError
            Provided testing framework has not been registered.
        """
        cls = self.frameworks[framework]
        return cls(widget, tempfilename)
