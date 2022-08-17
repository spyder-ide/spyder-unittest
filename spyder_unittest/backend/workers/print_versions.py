# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Script for checking which test frameworks are installed.

This script prints a dictionary with the required info to stdout.
"""


def get_pytest_info():
    """Return information about pytest."""
    try:
        import pytest
    except ImportError:
        return {'available': False}

    plugins = {}

    class GetPluginVersionsPlugin():
        def pytest_cmdline_main(self, config):
            nonlocal plugins
            plugininfo = config.pluginmanager.list_plugin_distinfo()
            plugins = {dist.project_name: dist.version
                       for plugin, dist in plugininfo}
            return 0  # stop pytest, don't collect or run tests

    # --capture=sys needed on Windows to avoid
    # ValueError: saved filedescriptor not valid anymore
    pytest.main(['--capture=sys'],
                plugins=[GetPluginVersionsPlugin()])

    return {'available': True,
            'version': pytest.__version__,
            'plugins': plugins}


def get_nose_info():
    """Return information about nose."""
    from pkg_resources import iter_entry_points
    try:
        import nose
    except ImportError:
        return {'available': False}

    plugins = {}
    for entry_point, _ in (nose.plugins.manager.EntryPointPluginManager
                           .entry_points):
        for ep in iter_entry_points(entry_point):
            plugins[ep.dist.project_name] = ep.dist.version

    return {'available': True,
            'version': nose.__version__,
            'plugins': plugins}


def get_unittest_info():
    """
    Return versions of framework and its plugins.

    As 'unittest' is a built-in framework, we use the python version.
    """
    from platform import python_version
    return {'available': True,
            'version': python_version(),
            'plugins': {}}


def get_all_info():
    """
    Return information about all testing frameworks.

    Information is returned as a dictionary like the following:
    {'pytest': {'available': True, 'version': '7.1.1',
                'plugins': {'flaky': '3.7.0', 'pytest-mock': '3.6.1'}},
     'nose': {'available': False},
     'unittest': {'available': True, 'version': '3.10.5', 'plugins': {}}}
    """
    return {'pytest': get_pytest_info(),
            'nose': get_nose_info(),
            'unittest': get_unittest_info()}


if __name__ == '__main__':
    print(get_all_info())
