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

import time

# Third-party imports
from qtpy.QtWidgets import QApplication
import pytest

# QtWebEngineWidgets must be imported
# before a QCoreApplication instance is created
from qtpy import QtWebEngineWidgets  # noqa

# Spyder imports
from spyder import version_info as spyder_version_info
from spyder.api.plugin_registration.registry import PLUGIN_REGISTRY
from spyder.app import start
from spyder.config.base import running_in_ci
from spyder.config.manager import CONF


@pytest.fixture
def main_window(monkeypatch):
    """Main Window fixture"""

    # Don't show tours message
    CONF.set('tours', 'show_tour_message', False)
    QApplication.processEvents()

    # Start the window
    window = start.main()
    QApplication.processEvents()

    yield window

    # This is to prevent "QThread: Thread still running" error
    if running_in_ci():
        time.sleep(5)
        QApplication.processEvents()

    # Close main window
    window.closing(close_immediately=True)
    window.close()
    CONF.reset_to_defaults(notification=False)
    CONF.reset_manager()
    PLUGIN_REGISTRY.reset()
