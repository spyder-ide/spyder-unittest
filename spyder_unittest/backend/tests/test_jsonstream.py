# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for jsonstream.py"""

# Standard library imports
from io import StringIO

# Local imports
from spyder_unittest.backend.jsonstream import JSONStreamWriter


def test_jsonstreamwriter_with_list():
    stream = StringIO()
    writer = JSONStreamWriter(stream)
    writer.write([1, 2])
    assert writer.stream.getvalue() == '6\n[1, 2]\n'


def test_jsonstreamwriter_with_unicode():
    stream = StringIO()
    writer = JSONStreamWriter(stream)
    writer.write('三')
    assert writer.stream.getvalue() == '8\n"\\u4e09"\n'
