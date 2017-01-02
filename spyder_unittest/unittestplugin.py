# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Spyder Project Developers
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Unit testing Plugin."""

# Standard library imports
import os.path

# Third party imports
from qtpy.QtCore import Signal
from spyder.config.base import get_translation
from spyder.plugins import SpyderPluginMixin
from spyder.utils import icon_manager as ima
from spyder.utils.qthelpers import create_action

# Local imports
from .widgets.configdialog import Config
from .widgets.unittestgui import UnitTestWidget, is_unittesting_installed

_ = get_translation("unittest", dirname="spyder_unittest")


class UnitTestWidgetInSpyder(UnitTestWidget):
    """
    Unit test widget for use inside Spyder.

    This class overrides some functions in `UnitTestWidget` to provide better
    integration with Spyder.
    """

    def __init__(self, parent=None):
        """Constructor."""
        UnitTestWidget.__init__(self, parent)

    def get_pythonpath(self):
        """
        Return directories to be added to the Python path.

        Use Python path from Spyder. Overrides function in base class.

        Returns
        -------
        list of str
        """
        return self.main.get_spyder_pythonpath()

    def get_default_config(self):
        """
        Return configuration which is proposed when current config is invalid.

        Propose to use directory of current file as working directory for
        testing.
        """
        filename = self.main.editor.get_current_filename()
        dirname = os.path.dirname(filename)
        return Config(wdir=dirname)


class UnitTestPlugin(UnitTestWidgetInSpyder, SpyderPluginMixin):
    """Unit testing."""

    CONF_SECTION = 'unittest'
    edit_goto = Signal(str, int, str)

    def __init__(self, parent=None):
        """Unit testing."""
        UnitTestWidgetInSpyder.__init__(self, parent=parent)
        SpyderPluginMixin.__init__(self, parent)

        # Initialize plugin
        self.initialize_plugin()

    # ----- SpyderPluginWidget API --------------------------------------------
    def get_plugin_title(self):
        """Return widget title."""
        return _("Unit testing")

    def get_plugin_icon(self):
        """Return widget icon."""
        return ima.icon('profiler')

    def get_focus_widget(self):
        """Return the widget to give focus to this dockwidget when raised."""
        return self.datatree

    def get_plugin_actions(self):
        """Return a list of actions related to plugin."""
        return []

    def on_first_registration(self):
        """Action to be performed on first plugin registration."""
        self.main.tabify_plugins(self.main.help, self)
        self.dockwidget.hide()

    def register_plugin(self):
        """Register plugin in Spyder's main window."""
        self.edit_goto.connect(self.main.editor.load)
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
        super(UnitTestPlugin, self).maybe_configure_and_start()
