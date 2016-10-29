# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Tests for unittestgui.py"""

import os

from qtpy.QtCore import Qt

from spyder.utils.qthelpers import qapplication
MAIN_APP = qapplication() # without this line, the import below segfaults

from spyder_unittest.widgets.unittestgui import UnitTestWidget

def test_run_tests_and_display_results(qtbot, tmpdir):
    os.chdir(tmpdir.strpath)
    testfilename = tmpdir.join('test_foo.py').strpath
    with open(testfilename, 'w') as f:
        f.write("def test_ok(): assert 1+1 == 2\n"
                "def test_fail(): assert 1+1 == 3\n")

    widget = UnitTestWidget(None)
    qtbot.addWidget(widget)
    widget.analyze(tmpdir.strpath)
    qtbot.wait(1000) # wait for tests to run

    datatree = widget.datatree
    assert datatree.topLevelItemCount() == 2
    assert datatree.topLevelItem(0).data(0, Qt.DisplayRole) == 'ok'
    assert datatree.topLevelItem(0).data(1, Qt.DisplayRole) == 'test_foo.test_ok'
    assert datatree.topLevelItem(0).data(2, Qt.DisplayRole) is None
    assert datatree.topLevelItem(1).data(0, Qt.DisplayRole) == 'failure'
    assert datatree.topLevelItem(1).data(1, Qt.DisplayRole) == 'test_foo.test_fail'
    assert datatree.topLevelItem(1).data(2, Qt.DisplayRole) == 'assert (1 + 1) == 3'
