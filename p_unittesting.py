# -*- coding:utf-8 -*-
#
# Copyright © 2013 Joseph Martinot-Lagarde
# based on p_profiler.py by Santiago Jaramillo
#
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Unit testing Plugin"""

from spyderlib.qt.QtGui import QVBoxLayout, QGroupBox, QLabel
from spyderlib.qt.QtCore import SIGNAL, Qt

# Local imports
from spyderlib.baseconfig import get_translation
_ = get_translation("p_unittesting", dirname="spyderplugins")
from spyderlib.utils.qthelpers import get_icon, create_action
from spyderlib.plugins import SpyderPluginMixin, PluginConfigPage, runconfig
from spyderlib.py3compat import configparser
from spyderplugins.widgets.unittestinggui import (UnitTestingWidget,
                                                  is_unittesting_installed)


class UnitTestingConfigPage(PluginConfigPage):
    """Widget with configuration options for unit testing
    """
    def setup_page(self):

        settings_group = QGroupBox(_("Settings"))
        use_color_box = self.create_checkbox(
            _("Use deterministic colors to differentiate functions"),
            'use_colors', default=True)

        results_group = QGroupBox(_("Results"))
        results_label1 = QLabel(_("Unit testing plugin results "
                                  "(the output of kernprof.py)\n"
                                  "are stored here:"))
        results_label1.setWordWrap(True)

        # Warning: do not try to regroup the following QLabel contents with
        # widgets above -- this string was isolated here in a single QLabel
        # on purpose: to fix Issue 863 of Profiler plugon
        results_label2 = QLabel(UnitTestingWidget.DATAPATH)

        results_label2.setTextInteractionFlags(Qt.TextSelectableByMouse)
        results_label2.setWordWrap(True)

        settings_layout = QVBoxLayout()
        settings_layout.addWidget(use_color_box)
        settings_group.setLayout(settings_layout)

        results_layout = QVBoxLayout()
        results_layout.addWidget(results_label1)
        results_layout.addWidget(results_label2)
        results_group.setLayout(results_layout)

        vlayout = QVBoxLayout()
        vlayout.addWidget(settings_group)
        vlayout.addWidget(results_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)


class UnitTesting(UnitTestingWidget, SpyderPluginMixin):
    """Unit testing"""
    CONF_SECTION = 'unittesting'
    CONFIGWIDGET_CLASS = UnitTestingConfigPage

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
        self.main.tabify_plugins(self.main.inspector, self)
        self.dockwidget.hide()

    def register_plugin(self):
        """Register plugin in Spyder's main window"""
        self.connect(self, SIGNAL("edit_goto(QString,int,QString)"),
                     self.main.editor.load)
        self.connect(self, SIGNAL('redirect_stdio(bool)'),
                     self.main.redirect_internalshell_stdio)
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

        try:
            use_colors = self.get_option('use_colors')
        except configparser.NoOptionError:
            use_colors = self.set_option('use_colors', True)
            use_colors = True

        UnitTestingWidget.analyze(self, filename, wdir=wdir, args=args,
                                  pythonpath=pythonpath,
                                  use_colors=use_colors)


#==============================================================================
# The following statements are required to register this 3rd party plugin:
#==============================================================================
PLUGIN_CLASS = UnitTesting
