# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Unit testing Plugin."""

# Third party imports
from qtpy.QtWidgets import QVBoxLayout
from spyder.config.base import get_translation
from spyder.plugins import SpyderPluginWidget
from spyder.py3compat import getcwd
from spyder.utils import icon_manager as ima
from spyder.utils.qthelpers import create_action

# Local imports
from .widgets.unittestgui import UnitTestWidget, is_unittesting_installed

_ = get_translation("unittest", dirname="spyder_unittest")


class UnitTestPlugin(SpyderPluginWidget):
    """Spyder plugin for unit testing."""

    CONF_SECTION = 'unittest'

    def __init__(self, parent=None):
        """Initialize plugin and corresponding widget."""
        SpyderPluginWidget.__init__(self, parent)
        self.main = parent  # Spyder 3 compatibility

        # Create unit test widget
        self.unittestwidget = UnitTestWidget(self.main)
        self.update_pythonpath()
        self.update_default_wdir()

        # Connect to relevant signals
        self.main.sig_pythonpath_changed.connect(self.update_pythonpath)
        self.main.workingdirectory.set_explorer_cwd.connect(
            self.update_default_wdir)
        self.main.projects.sig_project_created.connect(
            self.update_default_wdir)
        self.main.projects.sig_project_loaded.connect(self.update_default_wdir)
        self.main.projects.sig_project_closed.connect(self.update_default_wdir)

        # Add unit test widget in dockwindow
        layout = QVBoxLayout()
        layout.addWidget(self.unittestwidget)
        self.setLayout(layout)

        # Initialize plugin
        self.initialize_plugin()

    def update_pythonpath(self):
        """
        Update Python path used to run unit tests.

        This function is called whenever the Python path set in Spyder changes.
        It synchronizes the Python path in the unittest widget with the Python
        path in Spyder.
        """
        self.unittestwidget.pythonpath = self.main.get_spyder_pythonpath()

    def update_default_wdir(self):
        """
        Update default working dir for running unit tests.

        The default working dir for running unit tests is set to the project
        directory if a project is open, or the current working directory if no
        project is opened. This function is called whenever this directory may
        change.
        """
        wdir = self.main.projects.get_active_project_path()
        if not wdir:  # if no project opened
            wdir = getcwd()
        self.unittestwidget.default_wdir = wdir

    # ----- SpyderPluginWidget API --------------------------------------------
    def get_plugin_title(self):
        """Return widget title."""
        return _("Unit testing")

    def get_plugin_icon(self):
        """Return widget icon."""
        return ima.icon('profiler')

    def get_focus_widget(self):
        """Return the widget to give focus to this dockwidget when raised."""
        return self.unittestwidget.datatree

    def get_plugin_actions(self):
        """Return a list of actions related to plugin."""
        return []

    def on_first_registration(self):
        """Action to be performed on first plugin registration."""
        self.main.tabify_plugins(self.main.help, self)
        self.dockwidget.hide()

    def register_plugin(self):
        """Register plugin in Spyder's main window."""
        self.main.add_dockwidget(self)

        unittesting_act = create_action(
            self,
            _("Run unit tests"),
            icon=ima.icon('profiler'),
            shortcut="Shift+Alt+F11",
            triggered=self.maybe_configure_and_start)
        unittesting_act.setEnabled(is_unittesting_installed())

        self.main.run_menu_actions += [unittesting_act]
        self.main.editor.pythonfile_dependent_actions += [unittesting_act]

    def refresh_plugin(self):
        """Refresh unit testing widget."""
        pass

    def closing_plugin(self, cancelable=False):
        """Perform actions before parent main window is closed."""
        return True

    def apply_plugin_settings(self, options):
        """Apply configuration file's plugin settings."""
        pass

    # ----- Public API --------------------------------------------------------
    def maybe_configure_and_start(self):
        """
        Ask for configuration if necessary and then run tests.

        Raise unittest widget. If the current test configuration is
        not valid (or not set), then ask the user to configure. Then
        run the tests.
        """
        if self.dockwidget and not self.ismaximized:
            self.dockwidget.setVisible(True)
            self.dockwidget.setFocus()
            self.dockwidget.raise_()
        self.unittestwidget.maybe_configure_and_start()
