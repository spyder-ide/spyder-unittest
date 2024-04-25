# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2023- Spyder Project Contributors
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------

# Standard library imports
import sys
import types
from unittest.mock import Mock, MagicMock

# Third party imports
from qtpy.QtWidgets import QWidget, QMainWindow
import pytest

# Spyder imports
from spyder.api.plugins import Plugins
from spyder.api.plugin_registration.registry import PLUGIN_REGISTRY
from spyder.app.cli_options import get_options
from spyder.config.manager import CONF

# Local imports
from spyder_unittest.unittestplugin import UnitTestPlugin


# -----------------------------------------------------------------------------
#
# Classes and fixtures copied from spyder/plugins/preferences/tests/conftest.py

class MainWindowMock(QMainWindow):
    register_shortcut = Mock()

    def __init__(self, parent):
        # This import assumes that an QApplication is already running,
        # so we can not put it at the top of the file
        from spyder.plugins.preferences.plugin import Preferences

        super().__init__(parent)
        self.default_style = None
        self.widgetlist = []
        self.thirdparty_plugins = []
        self.shortcut_data = []
        self.prefs_dialog_instance = None
        self._APPLICATION_TOOLBARS = MagicMock()

        self.console = Mock()

        # To provide command line options for plugins that need them
        sys_argv = [sys.argv[0]]  # Avoid options passed to pytest
        self._cli_options = get_options(sys_argv)[0]

        PLUGIN_REGISTRY.reset()
        PLUGIN_REGISTRY.sig_plugin_ready.connect(self.register_plugin)
        PLUGIN_REGISTRY.register_plugin(self, Preferences)

        # Load shortcuts for tests
        for context, name, __ in CONF.iter_shortcuts():
            self.shortcut_data.append((None, context, name, None, None))

        for attr in ['mem_status', 'cpu_status']:
            mock_attr = Mock()
            setattr(mock_attr, 'toolTip', lambda: '')
            setattr(mock_attr, 'setToolTip', lambda x: '')
            setattr(mock_attr, 'prefs_dialog_instance', lambda: '')
            setattr(self, attr, mock_attr)

    def register_plugin(self, plugin_name, external=False):
        plugin = PLUGIN_REGISTRY.get_plugin(plugin_name)
        plugin._register(omit_conf=True)

    def get_plugin(self, plugin_name, error=True):
        if plugin_name in PLUGIN_REGISTRY:
            return PLUGIN_REGISTRY.get_plugin(plugin_name)


class ConfigDialogTester(QWidget):
    def __init__(self, parent, main_class,
                 general_config_plugins, plugins):
        # This import assumes that an QApplication is already running,
        # so we can not put it at the top of the file
        from spyder.plugins.preferences.plugin import Preferences

        super().__init__(parent)
        self._main = main_class(self) if main_class else None
        if self._main is None:
            self._main = MainWindowMock(self)

        def register_plugin(self, plugin_name, external=False):
            plugin = PLUGIN_REGISTRY.get_plugin(plugin_name)
            plugin._register()

        def get_plugin(self, plugin_name, error=True):
            if plugin_name in PLUGIN_REGISTRY:
                return PLUGIN_REGISTRY.get_plugin(plugin_name)
            return None

        # Commented out because it gives the error:
        #     A plugin with section "unittest" already exists!
        # setattr(self._main, 'register_plugin',
        #         types.MethodType(register_plugin, self._main))
        setattr(self._main, 'get_plugin',
                types.MethodType(get_plugin, self._main))

        PLUGIN_REGISTRY.reset()
        PLUGIN_REGISTRY.sig_plugin_ready.connect(self._main.register_plugin)
        print(f'ConfigDialogTester registering {Preferences=}')
        PLUGIN_REGISTRY.register_plugin(self._main, Preferences)

        if plugins:
            for Plugin in plugins:
                if hasattr(Plugin, 'CONF_WIDGET_CLASS'):
                    for required in (Plugin.REQUIRES or []):
                        if required not in PLUGIN_REGISTRY:
                            PLUGIN_REGISTRY.plugin_registry[required] = MagicMock()

                    PLUGIN_REGISTRY.register_plugin(self._main, Plugin)
                else:
                    plugin = Plugin(self._main)
                    preferences = self._main.get_plugin(Plugins.Preferences)
                    preferences.register_plugin_preferences(plugin)


@pytest.fixture
def config_dialog(qtbot, request):
    # mocker.patch.object(ima, 'icon', lambda x, *_: QIcon())
    # Above line commented out from source because it gave an error

    main_class, general_config_plugins, plugins = request.param

    main_ref = ConfigDialogTester(
        None, main_class, general_config_plugins, plugins)
    qtbot.addWidget(main_ref)

    preferences = main_ref._main.get_plugin(Plugins.Preferences)
    preferences.open_dialog()
    container = preferences.get_container()
    dlg = container.dialog

    yield dlg

    dlg.close()


# -----------------------------------------------------------------------------
#
# Test for the spyder-unittest plugin

@pytest.mark.parametrize(
    'config_dialog',
    [[MainWindowMock, [], [UnitTestPlugin]]],
    indirect=True)
def test_unittestconfigpage(config_dialog):
    """Test that changing "Abbreviate test names" works as expected."""
    # Get reference to Preferences dialog and widget page to interact with
    dlg = config_dialog
    widget = config_dialog.get_page()

    # Assert default value of option in True
    assert widget.get_option('abbrev_test_names') is False

    # Toggle checkbox and assert that option value is now False
    widget.abbrev_box.click()
    dlg.apply_btn.click()
    assert widget.get_option('abbrev_test_names') is True

    # Reset options to default and check that option value is True again
    # Note: it is necessary to specify the section in reset_to_defaults()
    CONF.reset_to_defaults(section='unittest', notification=False)
    assert widget.get_option('abbrev_test_names') is False
