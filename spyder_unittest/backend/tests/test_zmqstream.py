# -*- coding: utf-8 -*-
#
# Copyright © 2018 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for zmqstream.py"""

# Local imports
from spyder_unittest.backend.zmqstream import ZmqStreamReader, ZmqStreamWriter


def test_zmqstream(qtbot):
    manager = ZmqStreamReader()
    worker = ZmqStreamWriter(manager.port)
    with qtbot.waitSignal(manager.sig_received) as blocker:
        worker.write(42)
    assert blocker.args == [[42]]
    worker.close()
    manager.close()
