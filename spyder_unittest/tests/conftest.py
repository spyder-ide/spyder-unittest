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

# Third-party imports
from qtpy.QtWidgets import QApplication
import pytest

# QtWebEngineWidgets must be imported
# before a QCoreApplication instance is created
from qtpy import QtWebEngineWidgets  # noqa

# Spyder imports
from spyder.app import start
from spyder.config.manager import CONF


@pytest.fixture
def main_window(request):
    """Main Window fixture"""

    # Don't show tours message
    CONF.set('tours', 'show_tour_message', False)
    QApplication.processEvents()

    from spyder.api.plugin_registration.registry import PLUGIN_REGISTRY
    PLUGIN_REGISTRY.reset()

    # Start the window
    window = start.main()
    QApplication.processEvents()

    yield window

    # Close main window
    window.close()
    CONF.reset_to_defaults(notification=False)
