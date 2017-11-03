# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for pytestworker.py"""

# Standard library imports
import os

# Local imports
from spyder_unittest.backend.jsonstream import JSONStreamWriter
from spyder_unittest.backend.pytestworker import SpyderPlugin, main

try:
    from unittest.mock import call, create_autospec, Mock
except ImportError:
    from mock import call, create_autospec, Mock  # Python 2


class EmptyClass:
    pass


def test_spyderplugin_test_collected():
    mock_writer = create_autospec(JSONStreamWriter)
    plugin = SpyderPlugin(mock_writer)
    testitem = EmptyClass()
    testitem.name = 'foo'
    testitem.parent = EmptyClass()
    testitem.parent.name = 'bar'
    plugin.pytest_itemcollected(testitem)
    mock_writer.write.assert_called_once_with({
        'event': 'collected',
        'name': 'foo',
        'module': 'bar'
    })


def test_pytestworker_integration(monkeypatch, tmpdir):
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath
    with open(testfilename, 'w') as f:
        f.write("def test_ok(): assert 1+1 == 2\n"
                "def test_fail(): assert 1+1 == 3\n")

    mock_writer = create_autospec(JSONStreamWriter)
    MockJSONStreamWriter = Mock(return_value=mock_writer)
    monkeypatch.setattr(
        'spyder_unittest.backend.pytestworker.JSONStreamWriter',
        MockJSONStreamWriter)
    main([testfilename])

    expected = [
        call({
            'event': 'collected',
            'name': 'test_ok',
            'module': 'test_foo.py'
        }), call({
            'event': 'collected',
            'name': 'test_fail',
            'module': 'test_foo.py'
        })
    ]
    assert mock_writer.write.call_args_list == expected
