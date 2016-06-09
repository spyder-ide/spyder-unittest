# -*- coding:utf-8 -*-
#
# Copyright © 2013 Joseph Martinot-Lagarde
# based on p_profiler.py by Santiago Jaramillo
#
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Unit testing Plugin"""

from qtpy.QtWidgets import QVBoxLayout, QGroupBox, QLabel
from qtpy.QtCore import Signal, Qt

# Local imports
from spyderlib.config.base import get_translation
_ = get_translation("unittesting", dirname="spyder_unittesting")
from spyderlib.utils.qthelpers import get_icon, create_action
from spyderlib.plugins import SpyderPluginMixin, runconfig
from .widgets.unittestinggui import (UnitTestingWidget, is_unittesting_installed)


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
        return get_icon('profiler.png')

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
        self.redirect_stdio.connect(self.main.redirect_internalshell_stdio)
        self.main.add_dockwidget(self)

        unittesting_act = create_action(self, _("Run unit tests"),
                                        icon=get_icon('profiler.png'),
                                        triggered=self.run_unittesting)
        unittesting_act.setEnabled(is_unittesting_installed())
        self.register_shortcut(unittesting_act, context="Unit testing",
                               name="Run unit tests", default="Ctrl+Shift+F10")

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
        self.analyze(self.main.editor.get_current_filename())

    def analyze(self, filename):
        """Reimplement analyze method"""
        if self.dockwidget and not self.ismaximized:
            self.dockwidget.setVisible(True)
            self.dockwidget.setFocus()
            self.dockwidget.raise_()
        pythonpath = self.main.get_spyder_pythonpath()
        runconf = runconfig.get_run_configuration(filename)
        wdir, args = None, None
        if runconf is not None:
            if runconf.wdir_enabled:
                wdir = runconf.wdir
            if runconf.args_enabled:
                args = runconf.args

        UnitTestingWidget.analyze(self, filename, wdir=wdir, args=args,
                                  pythonpath=pythonpath)
