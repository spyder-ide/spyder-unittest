# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Support for Nose framework."""

# Local imports
from spyder_unittest.backend.runnerbase import RunnerBase


class NoseRunner(RunnerBase):
    """Class for running tests within Nose framework."""

    module = 'nose'
    name = 'nose'

    def create_argument_list(self):
        """Create argument list for testing process."""
        return ['--with-xunit', '--xunit-file={}'.format(self.resultfilename)]
