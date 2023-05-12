# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Tests for the integration of the plugin with Spyder.

All tests needs to be decorated with pytest.mark.order('last') to ensure
that they are executed after all other tests because monkeypatching
functions inside the plugin does not work after running these tests.

The reason for this is not clear, but it may have to do with how plugins
are imported in spyder/otherplugins.py.
"""

# Standard library imports
from collections import OrderedDict
import os

# Third party imports
import pytest
from qtpy.QtCore import Qt

# Spyder imports
from spyder.api.plugins import Plugins
from spyder.plugins.mainmenu.api import ApplicationMenus

# Local imports
from spyder_unittest.unittestplugin import UnitTestPlugin
from spyder_unittest.widgets.configdialog import Config


def test_menu_item(main_window):
    """
    Test that plugin adds item 'Run unit tests' to Run menu.
    """
    main_menu = main_window.get_plugin(Plugins.MainMenu)
    run_menu = main_menu.get_application_menu(ApplicationMenus.Run)

    # Filter out seperators (indicated by action is None) and convert to text
    menu_items = [action.text() for action in run_menu.get_actions() if action]

    assert 'Run unit tests' in menu_items


def test_pythonpath_change(main_window):
    """
    Test that pythonpath changes in Spyder propagate to UnitTestWidget.
    """
    ppm = main_window.get_plugin(Plugins.PythonpathManager)
    unittest_plugin = main_window.get_plugin(UnitTestPlugin.NAME)

    new_path = '/some/path'
    new_path_dict = OrderedDict([(new_path, True)])
    ppm.get_container()._update_python_path(new_path_dict)

    assert unittest_plugin.get_widget().pythonpath == [new_path]


def test_default_working_dir(main_window, tmpdir):
    """
    Test that plugin's default working dir is current working directory.
    After creating a project, the plugin's default working dir should be the
    same as the project directory. When the project is closed again, the 
    plugin's default working dir should revert back to the current working
    directory.
    """
    projects = main_window.get_plugin(Plugins.Projects)
    unittest_plugin = main_window.get_plugin(UnitTestPlugin.NAME)
    project_dir = str(tmpdir)

    assert unittest_plugin.get_widget().default_wdir == os.getcwd()

    projects.create_project(project_dir)
    assert unittest_plugin.get_widget().default_wdir == project_dir

    projects.close_project()
    assert unittest_plugin.get_widget().default_wdir == os.getcwd()


def test_plugin_config(main_window, tmpdir, qtbot):
    """
    Test that plugin uses the project's config file if a project is open.
    """
    projects = main_window.get_plugin(Plugins.Projects)
    unittest_plugin = main_window.get_plugin(UnitTestPlugin.NAME)
    unittest_widget = unittest_plugin.get_widget()
    project_dir = str(tmpdir)
    config_file_path = tmpdir.join('.spyproject', 'config', 'unittest.ini')

    # Test config file does not exist and config is empty
    assert not config_file_path.check()
    assert unittest_widget.config is None

    # Open project
    projects.create_project(project_dir)

    # Test config file does exist but config is empty
    assert config_file_path.check()
    assert 'framework = ' in config_file_path.read().splitlines()
    assert unittest_widget.config is None

    # Set config and test that this is recorded in config file
    config = Config(framework='unittest', wdir=str(tmpdir))
    with qtbot.waitSignal(unittest_widget.sig_newconfig):
        unittest_widget.config = config
    assert 'framework = unittest' in config_file_path.read().splitlines()

    # Close project and test that config is empty
    projects.close_project()
    assert unittest_widget.config is None

    # Re-open project and test that config is correctly read
    projects.open_project(project_dir)
    assert unittest_widget.config == config

    # Close project before ending test, which removes the project dir
    projects.close_project()


def test_go_to_test_definition(main_window, tmpdir, qtbot):
    """
    Test that double clicking on a test result opens the file with the test
    definition in the editor with the cursor on the test definition.
    """
    unittest_plugin = main_window.get_plugin(UnitTestPlugin.NAME)
    unittest_widget = unittest_plugin.get_widget()
    model = unittest_widget.testdatamodel
    view = unittest_widget.testdataview

    # Write test file
    testdir_str = str(tmpdir)
    testfile_str = tmpdir.join('test_foo.py').strpath
    os.chdir(testdir_str)
    with open(testfile_str, 'w') as f:
        f.write("def test_ok(): assert 1+1 == 2\n"
                "def test_fail(): assert 1+1 == 3\n")

    # Run tests
    config = Config(wdir=testdir_str, framework='pytest', coverage=False)
    with qtbot.waitSignal(
            unittest_widget.sig_finished, timeout=10000, raising=True):
        unittest_widget.run_tests(config)

    # Check that row 1 corresponds to `test_fail`
    index = model.index(1, 1)
    point = view.visualRect(index).center()
    assert view.indexAt(point).data(Qt.DisplayRole).endswith('test_fail')

    # Double click on `test_fail`
    unittest_plugin.switch_to_plugin()
    with qtbot.waitSignal(view.sig_edit_goto):
        qtbot.mouseClick(view.viewport(), Qt.LeftButton, pos=point, delay=100)
        qtbot.mouseDClick(view.viewport(), Qt.LeftButton, pos=point)

    # Check that test file is opened in editor
    editor = main_window.get_plugin(Plugins.Editor)
    filename = editor.get_current_filename()
    assert filename == testfile_str
    
    # Check that cursor is on line defining `test_fail`
    cursor = editor.get_current_editor().textCursor()
    line = cursor.block().text()
    assert line.startswith('def test_fail')
