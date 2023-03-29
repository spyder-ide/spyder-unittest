# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for print_versions.py"""

from spyder_unittest.backend.workers.print_versions import (
    get_nose2_info, get_pytest_info, get_unittest_info)


def test_get_pytest_info_without_plugins(monkeypatch):
    import pytest
    monkeypatch.setattr(pytest, '__version__', '1.2.3')
    from _pytest.config import PytestPluginManager
    monkeypatch.setattr(
        PytestPluginManager,
        'list_plugin_distinfo', lambda _: ())
    expected = {'available': True, 'version': '1.2.3', 'plugins': {}}
    assert get_pytest_info() == expected


def test_get_pytest_info_with_plugins(monkeypatch):
    import pytest
    import pkg_resources
    monkeypatch.setattr(pytest, '__version__', '1.2.3')
    dist1 = pkg_resources.Distribution(project_name='myPlugin1',
                                       version='4.5.6')
    dist2 = pkg_resources.Distribution(project_name='myPlugin2',
                                       version='7.8.9')
    from _pytest.config import PytestPluginManager
    monkeypatch.setattr(
        PytestPluginManager,
        'list_plugin_distinfo', lambda _: (('1', dist1), ('2', dist2)))
    expected = {'available': True, 'version': '1.2.3',
                'plugins': {'myPlugin1': '4.5.6', 'myPlugin2': '7.8.9'}}
    assert get_pytest_info() == expected


def test_get_nose2_info(monkeypatch):
    import nose2
    monkeypatch.setattr(nose2, '__version__', '1.2.3')
    expected = {'available': True, 'version': '1.2.3', 'plugins': {}}
    assert get_nose2_info() == expected


def test_get_unittest_imfo(monkeypatch):
    import platform
    monkeypatch.setattr(platform, 'python_version', lambda: '1.2.3')
    expected = {'available': True, 'version': '1.2.3', 'plugins': {}}
    assert get_unittest_info() == expected
