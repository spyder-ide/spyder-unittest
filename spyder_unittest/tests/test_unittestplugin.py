# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for unittestplugin.py"""

# Third party imports
import pytest
from spyder.plugins.projects.api import EmptyProject

# Local imports
from spyder_unittest.unittestplugin import UnitTestPlugin
from spyder_unittest.widgets.configdialog import Config

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock  # Python 2


class PluginForTesting(UnitTestPlugin):
    CONF_FILE = False

    def __init__(self, parent):
        UnitTestPlugin.__init__(self, parent)


@pytest.fixture
def plugin(qtbot):
    """Set up the unittest plugin."""
    res = UnitTestPlugin(None, None)
    res._main = MagicMock()
    res._main.get_spyder_pythonpath = MagicMock(return_value='fakepythonpath')
    res.initialize()
    return res


@pytest.mark.skip('not clear how to test interactions between plugins')
def test_plugin_initialization(plugin):
    assert len(plugin.main.run_menu_actions) == 2
    assert plugin.main.run_menu_actions[1].text() == 'Run unit tests'


def test_plugin_pythonpath(plugin):
    # Test signal/slot connection
    plugin.get_main().sig_pythonpath_changed.connect.assert_called_with(
        plugin.update_pythonpath)

    # Test pythonpath is set to path provided by Spyder
    assert plugin.get_widget().pythonpath == 'fakepythonpath'

    # Test that change in path propagates
    plugin.get_main().get_spyder_pythonpath = MagicMock(
        return_value='anotherpath')
    plugin.update_pythonpath()
    assert plugin.get_widget().pythonpath == 'anotherpath'


@pytest.mark.skip('not clear how to test interactions between plugins')
def test_plugin_wdir(plugin, monkeypatch, tmpdir):
    # Test signal/slot connections
    plugin.main.workingdirectory.sig_current_directory_changed.connect.assert_called_with(
        plugin.update_default_wdir)
    plugin.main.projects.sig_project_created.connect.assert_called_with(
        plugin.handle_project_change)
    plugin.main.projects.sig_project_loaded.connect.assert_called_with(
        plugin.handle_project_change)
    plugin.main.projects.sig_project_closed.connect.assert_called_with(
        plugin.handle_project_change)

    # Test default_wdir is set to current working dir
    monkeypatch.setattr('spyder_unittest.unittestplugin.getcwd',
                        lambda: 'fakecwd')
    plugin.update_default_wdir()
    assert plugin.unittestwidget.default_wdir == 'fakecwd'

    # Test after opening project, default_wdir is set to project dir
    project = EmptyProject(str(tmpdir))
    plugin.main.projects.get_active_project = lambda: project
    plugin.main.projects.get_active_project_path = lambda: project.root_path
    plugin.handle_project_change()
    assert plugin.unittestwidget.default_wdir == str(tmpdir)

    # Test after closing project, default_wdir is set back to cwd
    plugin.main.projects.get_active_project = lambda: None
    plugin.main.projects.get_active_project_path = lambda: None
    plugin.handle_project_change()
    assert plugin.unittestwidget.default_wdir == 'fakecwd'


@pytest.mark.skip('not clear how to test interactions between plugins')
def test_plugin_config(plugin, tmpdir, qtbot):
    # Test config file does not exist and config is empty
    config_file_path = tmpdir.join('.spyproject', 'config', 'unittest.ini')
    assert not config_file_path.check()
    assert plugin.unittestwidget.config is None

    # Open project
    project = EmptyProject(str(tmpdir))
    plugin.main.projects.get_active_project = lambda: project
    plugin.main.projects.get_active_project_path = lambda: project.root_path
    plugin.handle_project_change()

    # Test config file does exist but config is empty
    assert config_file_path.check()
    assert 'framework = ' in config_file_path.read().splitlines()
    assert plugin.unittestwidget.config is None

    # Set config and test that this is recorded in config file
    config = Config(framework='unittest', wdir=str(tmpdir))
    with qtbot.waitSignal(plugin.unittestwidget.sig_newconfig):
        plugin.unittestwidget.config = config
    assert 'framework = unittest' in config_file_path.read().splitlines()

    # Close project and test that config is empty
    plugin.main.projects.get_active_project = lambda: None
    plugin.main.projects.get_active_project_path = lambda: None
    plugin.handle_project_change()
    assert plugin.unittestwidget.config is None

    # Re-open project and test that config is correctly read
    plugin.main.projects.get_active_project = lambda: project
    plugin.main.projects.get_active_project_path = lambda: project.root_path
    plugin.handle_project_change()
    assert plugin.unittestwidget.config == config


@pytest.mark.skip('not clear how to test interactions between plugins')
def test_plugin_goto_in_editor(plugin, qtbot):
    plugin.unittestwidget.sig_edit_goto.emit('somefile', 42)
    plugin.main.editor.load.assert_called_with('somefile', 43, '')
