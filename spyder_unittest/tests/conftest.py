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
from spyder import dependencies
from spyder import version_info as spyder_version_info
from spyder.api.plugin_registration.registry import PLUGIN_REGISTRY
from spyder.app import start
from spyder.config.manager import CONF

SPYDER6 = spyder_version_info[0] == 6


@pytest.fixture
def main_window(monkeypatch):
    """Main Window fixture"""

    if not SPYDER6:
        # Disable loading of old third-party plugins in Spyder 5
        monkeypatch.setattr(
            'spyder.app.mainwindow.get_spyderplugins_mods', lambda: [])

    # Don't show tours message
    CONF.set('tours', 'show_tour_message', False)
    QApplication.processEvents()

    # Reset global state
    dependencies.DEPENDENCIES = []
    PLUGIN_REGISTRY.reset()

    # Start the window
    window = start.main()
    QApplication.processEvents()

    yield window

    # Close main window
    window.close()
    CONF.reset_to_defaults(notification=False)
