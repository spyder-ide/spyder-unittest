# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Configuration file for Pytest.

This contains the necessary definitions to make the main_window fixture
available for integration tests.
"""

# Standard library imports
import os

# Third-party imports
import pytest

# This needs to be before any Spyder imports
os.environ['SPYDER_PYTEST'] = 'True'

# Spyder imports
from spyder.app.tests.conftest import main_window
from spyder.config.manager import CONF


# Copied from spyder/app/tests/conftest.py
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "rep_" + rep.when, rep)


# Copied from spyder/app/tests/conftest.py
@pytest.fixture(scope="session", autouse=True)
def cleanup(request, qapp):
    """Cleanup the testing setup once we are finished."""

    def close_window():
        # Close last used mainwindow and QApplication if needed
        if hasattr(main_window, 'window') and main_window.window is not None:
            window = main_window.window
            main_window.window = None
            window.close()
            window = None
            CONF.reset_to_defaults(notification=False)
        if qapp.instance():
            qapp.quit()

    request.addfinalizer(close_window)
