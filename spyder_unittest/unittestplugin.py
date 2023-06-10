# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Unit testing Plugin."""

# Standard library imports
from os import getcwd
import os.path as osp

# Third party imports
import qtawesome
from qtpy.QtCore import Qt

# Spyder imports
from spyder.api.plugins import Plugins, SpyderDockablePlugin
from spyder.api.plugin_registration.decorators import (
    on_plugin_available, on_plugin_teardown)
from spyder.config.base import get_translation
from spyder.config.gui import is_dark_interface
from spyder.plugins.mainmenu.api import ApplicationMenus
from spyder.utils.palette import SpyderPalette

# Local imports
from spyder_unittest.widgets.configdialog import Config
from spyder_unittest.widgets.confpage import UnitTestConfigPage
from spyder_unittest.widgets.unittestgui import UnitTestWidget

_ = get_translation('spyder_unittest')


class UnitTestPluginActions:
    Run = 'Run tests'


class UnitTestPlugin(SpyderDockablePlugin):
    """Spyder plugin for unit testing."""

    NAME = 'unittest'
    REQUIRES = []
    OPTIONAL = [Plugins.Editor, Plugins.MainMenu, Plugins.Preferences,
                Plugins.Projects, Plugins.PythonpathManager,
                Plugins.WorkingDirectory]
    TABIFY = [Plugins.VariableExplorer]
    WIDGET_CLASS = UnitTestWidget

    CONF_SECTION = NAME
    CONF_DEFAULTS = [(CONF_SECTION,
                      {'framework': '',
                       'wdir': '',
                       'coverage': False,
                       'abbrev_test_names': False}),
                     ('shortcuts',
                      {'unittest/Run tests': 'Alt+Shift+F11'})]
    CONF_NAMEMAP = {CONF_SECTION: [(CONF_SECTION,
                                    ['framework', 'wdir', 'coverage'])]}
    CONF_FILE = True
    CONF_VERSION = '0.2.0'
    CONF_WIDGET_CLASS = UnitTestConfigPage

    # --- Mandatory SpyderDockablePlugin methods ------------------------------

    @staticmethod
    def get_name():
        """
        Return the plugin localized name.

        Returns
        -------
        str
            Localized name of the plugin.
        """
        return _('Unit testing')

    def get_description(self):
        """
        Return the plugin localized description.

        Returns
        -------
        str
            Localized description of the plugin.
        """
        return _('Run test suites and view their results')

    def get_icon(self):
        """
        Return the plugin associated icon.

        Returns
        -------
        QIcon
            QIcon instance
        """
        return qtawesome.icon('mdi.test-tube', color=SpyderPalette.ICON_1)

    def on_initialize(self):
        """
        Setup the plugin.
        """
        self.get_widget().sig_newconfig.connect(self.save_config)

        self.create_action(
            UnitTestPluginActions.Run,
            text=_('Run unit tests'),
            tip=_('Run unit tests'),
            icon=self.get_icon(),
            triggered=self.maybe_configure_and_start,
            context=Qt.ApplicationShortcut,
            register_shortcut=True)

    # ----- Set up interactions with other plugins ----------------------------

    @on_plugin_available(plugin=Plugins.Editor)
    def on_editor_available(self):
        """
        Set up interactions when Editor plugin available.

        Add 'Run unit tests' to context menu in editor for Python files.
        Save all files in editor before running tests.
        Go to test definition in editor on double click in unit test plugin.
        """
        editor = self.get_plugin(Plugins.Editor)
        run_action = self.get_action(UnitTestPluginActions.Run)
        editor.pythonfile_dependent_actions += [run_action]
        # FIXME: Previous line does not do anything
        self.get_widget().pre_test_hook = editor.save_all
        self.get_widget().sig_edit_goto.connect(self.goto_in_editor)

    @on_plugin_teardown(plugin=Plugins.Editor)
    def on_editor_teardown(self):
        """
        Disconnect from Editor plugin.
        """
        self.get_widget().pre_test_hook = None
        self.get_widget().sig_edit_goto.disconnect(self.goto_in_editor)

    @on_plugin_available(plugin=Plugins.MainMenu)
    def on_main_menu_available(self):
        """
        Add 'Run unit tests' menu item when MainMenu plugin available.
        """
        mainmenu = self.get_plugin(Plugins.MainMenu)
        run_action = self.get_action(UnitTestPluginActions.Run)
        mainmenu.add_item_to_application_menu(
            run_action, menu_id=ApplicationMenus.Run)

    @on_plugin_teardown(plugin=Plugins.MainMenu)
    def on_main_menu_teardown(self):
        """
        Remove 'Run unit tests; menu item from the application menu.
        """
        mainmenu = self.get_plugin(Plugins.MainMenu)
        mainmenu.remove_item_from_application_menu(
            UnitTestPluginActions.Run, menu_id=ApplicationMenus.Run)

    @on_plugin_available(plugin=Plugins.Preferences)
    def on_preferences_available(self):
        """
        Use config when Preferences plugin available.

        Specifically, register the unittest plugin preferences, and find out
        whether Spyder uses a dark interface and communicate this to the
        unittest widget.
        """
        preferences = self.get_plugin(Plugins.Preferences)
        preferences.register_plugin_preferences(self)
        self.get_widget().use_dark_interface(is_dark_interface())

    @on_plugin_teardown(plugin=Plugins.Preferences)
    def on_preferences_teardown(self):
        """
        De-register unittest plugin preferences.
        """
        preferences = self.get_plugin(Plugins.Preferences)
        preferences.deregister_plugin_preferences(self)

    @on_plugin_available(plugin=Plugins.Projects)
    def on_projects_available(self):
        """
        Connect when Projects plugin available.

        Connect to signals emitted when the current project changes.
        """
        projects = self.get_plugin(Plugins.Projects)
        projects.sig_project_created.connect(self.handle_project_change)
        projects.sig_project_loaded.connect(self.handle_project_change)
        projects.sig_project_closed.connect(self.handle_project_change)

    @on_plugin_teardown(plugin=Plugins.Projects)
    def on_projects_teardown(self):
        """
        Disconnect from Projects plugin.
        """
        projects = self.get_plugin(Plugins.Projects)
        projects.sig_project_created.disconnect(self.handle_project_change)
        projects.sig_project_loaded.disconnect(self.handle_project_change)
        projects.sig_project_closed.disconnect(self.handle_project_change)

    @on_plugin_available(plugin=Plugins.PythonpathManager)
    def on_pythonpath_manager_available(self):
        """
        Connect to signal announcing that Python path changed.
        """
        ppm = self.get_plugin(Plugins.PythonpathManager)
        ppm.sig_pythonpath_changed.connect(self.update_pythonpath)

    @on_plugin_teardown(plugin=Plugins.PythonpathManager)
    def on_pythonpath_manager_teardown(self):
        """
        Disconnect from PythonpathManager plugin.
        """
        ppm = self.get_plugin(Plugins.PythonpathManager)
        ppm.sig_pythonpath_changed.disconnect(self.update_pythonpath)

    @on_plugin_available(plugin=Plugins.WorkingDirectory)
    def on_working_directory_available(self):
        """
        Connect when WorkingDirectory plugin available.

        Find out what the current working directory is and connect to the
        signal emitted when the current working directory changes.
        """
        working_directory = self.get_plugin(Plugins.WorkingDirectory)
        working_directory.sig_current_directory_changed.connect(
            self.update_default_wdir)
        self.update_default_wdir()

    @on_plugin_teardown(plugin=Plugins.WorkingDirectory)
    def on_working_directory_teardown(self):
        """
        Disconnect from WorkingDirectory plugin.
        """
        working_directory = self.get_plugin(Plugins.WorkingDirectory)
        working_directory.sig_current_directory_changed.disconnect(
            self.update_default_wdir)

    # --- UnitTestPlugin methods ----------------------------------------------

    def update_pythonpath(self):
        """
        Update Python path used to run unit tests.

        This function is called whenever the Python path set in Spyder changes.
        It synchronizes the Python path in the unittest widget with the Python
        path in Spyder.
        """
        ppm = self.get_plugin(Plugins.PythonpathManager)
        self.get_widget().pythonpath = ppm.get_spyder_pythonpath()

    def handle_project_change(self):
        """
        Handle the event where the current project changes.

        This updates the default working directory for running tests and loads
        the test configuration from the project preferences.
        """
        self.update_default_wdir()
        self.load_config()

    def update_default_wdir(self):
        """
        Update default working dir for running unit tests.

        The default working dir for running unit tests is set to the project
        directory if a project is open, or the current working directory if no
        project is opened. This function is called whenever this directory may
        change.
        """
        projects = self.get_plugin(Plugins.Projects)
        if projects:
            wdir = projects.get_active_project_path()
            if not wdir:  # if no project opened
                wdir = getcwd()
        else:
            wdir = getcwd()
        self.get_widget().default_wdir = wdir

    def load_config(self):
        """
        Load test configuration from project preferences.

        If the test configuration stored in the project preferences is valid,
        then use it. If it is not valid (e.g., because the user never
        configured testing for this project) or no project is opened, then
        invalidate the current test configuration.

        If necessary, patch the project preferences to include this plugin's
        config options.
        """
        widget = self.get_widget()
        projects_plugin = self.get_plugin(Plugins.Projects)
        if projects_plugin:
            project = projects_plugin.get_active_project()
        else:
            project = None

        if not project:
            widget.set_config_without_emit(None)
            return

        if self.CONF_SECTION not in project.config._name_map:
            project.config._name_map = project.config._name_map.copy()
            project.config._name_map.update(self.CONF_NAMEMAP)

        if self.CONF_SECTION not in project.config._configs_map:
            config_class = project.config.get_config_class()
            path = osp.join(project.root_path, '.spyproject', 'config')
            conf = config_class(
                name=self.CONF_SECTION,
                defaults=self.CONF_DEFAULTS,
                path=path,
                load=True,
                version=self.CONF_VERSION)
            project.config._configs_map[self.CONF_SECTION] = conf

        new_config = Config(
            framework=project.get_option('framework', self.CONF_SECTION),
            wdir=project.get_option('wdir', self.CONF_SECTION),
            coverage=project.get_option('coverage', self.CONF_SECTION))
        if not widget.config_is_valid(new_config):
            new_config = None
        widget.set_config_without_emit(new_config)

    def save_config(self, test_config):
        """
        Save test configuration in project preferences.

        If no project is opened, then do not save.
        """
        projects_plugin = self.get_plugin(Plugins.Projects)
        if not projects_plugin:
            return
        project = projects_plugin.get_active_project()
        if not project:
            return
        project.set_option('framework', test_config.framework,
                           self.CONF_SECTION)
        project.set_option('wdir', test_config.wdir, self.CONF_SECTION)
        project.set_option('coverage', test_config.coverage, self.CONF_SECTION)

    def goto_in_editor(self, filename, lineno):
        """
        Go to specified line in editor.

        This function is called when the unittest widget emits `sig_edit_goto`.
        Note that the line number in the signal is zero based (the first line
        is line 0), but the editor expects a one-based line number.
        """
        editor_plugin = self.get_plugin(Plugins.Editor)
        if editor_plugin:
            editor_plugin.load(filename, lineno + 1, '')

    # ----- Public API --------------------------------------------------------

    def maybe_configure_and_start(self):
        """
        Ask for configuration if necessary and then run tests.

        Raise unittest widget. If the current test configuration is
        not valid (or not set), then ask the user to configure. Then
        run the tests.
        """
        self.switch_to_plugin()
        self.get_widget().maybe_configure_and_start()
