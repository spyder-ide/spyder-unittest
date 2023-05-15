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
from unittest.mock import patch
import pytest

# QtWebEngineWidgets must be imported
# before a QCoreApplication instance is created
from qtpy import QtWebEngineWidgets  # noqa

# Spyder imports
from spyder import dependencies
from spyder.api.plugin_registration.registry import PLUGIN_REGISTRY
from spyder.app import start
from spyder.config.manager import CONF


@pytest.fixture
def main_window():
    """Main Window fixture"""

    # Don't show tours message
    CONF.set('tours', 'show_tour_message', False)
    QApplication.processEvents()

    # Reset global state
    dependencies.DEPENDENCIES = []
    PLUGIN_REGISTRY.reset()

    # Start the window
    with patch('spyder.app.mainwindow.MainWindow.start_open_files_server'):
        window = start.main()
        QApplication.processEvents()

    yield window

    # Close main window
    window.close()
    window = None
    CONF.reset_to_defaults(notification=False)
