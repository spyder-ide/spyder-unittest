# -*- coding:utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Unit testing Plugin"""

import os.path as osp

from qtpy.QtCore import Signal

# Local imports
from spyder.config.base import get_translation
from spyder.utils.qthelpers import create_action
from spyder.utils import icon_manager as ima
from spyder.plugins import SpyderPluginMixin
from .widgets.unittestinggui import (UnitTestingWidget, is_unittesting_installed)

_ = get_translation("unittest", dirname="spyder_unittest")


class UnitTesting(UnitTestingWidget, SpyderPluginMixin):
    """Unit testing"""
    CONF_SECTION = 'unittesting'
    edit_goto = Signal(str, int, str)

    def __init__(self, parent=None):
        UnitTestingWidget.__init__(self, parent=parent)
        SpyderPluginMixin.__init__(self, parent)

        # Initialize plugin
        self.initialize_plugin()

    #------ SpyderPluginWidget API --------------------------------------------
    def get_plugin_title(self):
        """Return widget title"""
        return _("Unit testing")

    def get_plugin_icon(self):
        """Return widget icon"""
        return ima.icon('profiler')

    def get_focus_widget(self):
        """
        Return the widget to give focus to when
        this plugin's dockwidget is raised on top-level
        """
        return self.datatree

    def get_plugin_actions(self):
        """Return a list of actions related to plugin"""
        return []

    def on_first_registration(self):
        """Action to be performed on first plugin registration"""
        self.main.tabify_plugins(self.main.help, self)
        self.dockwidget.hide()

    def register_plugin(self):
        """Register plugin in Spyder's main window"""
        self.edit_goto.connect(self.main.editor.load)
        self.main.add_dockwidget(self)

        unittesting_act = create_action(
            self, _("Run unit tests"), icon=ima.icon('profiler'),
            shortcut="Shift+Alt+F11", triggered=self.run_unittesting)
        unittesting_act.setEnabled(is_unittesting_installed())

        self.main.run_menu_actions += [unittesting_act]
        self.main.editor.pythonfile_dependent_actions += [unittesting_act]

    def refresh_plugin(self):
        """Refresh unit testing widget"""
        pass

    def closing_plugin(self, cancelable=False):
        """Perform actions before parent main window is closed"""
        return True

    def apply_plugin_settings(self, options):
        """Apply configuration file's plugin settings"""
        pass

    #------ Public API --------------------------------------------------------
    def run_unittesting(self):
        """Run unit testing"""
        filename = self.main.editor.get_current_filename()
        dirname = osp.dirname(filename)
        self.analyze(dirname)

    def analyze(self, wdir):
        """Reimplement analyze method"""
        if self.dockwidget and not self.ismaximized:
            self.dockwidget.setVisible(True)
            self.dockwidget.setFocus()
            self.dockwidget.raise_()
        pythonpath = self.main.get_spyder_pythonpath()
        UnitTestingWidget.analyze(self, wdir, pythonpath=pythonpath)
