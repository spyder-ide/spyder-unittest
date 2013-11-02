#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
:author: Joseph Martinot-Lagarde

Created on Sat Jan 19 14:57:57 2013
"""

from __future__ import (
    print_function, division, unicode_literals, absolute_import)


import os
import pytest
from pymela import image


class TestImage(object):

    def test_ok(self):
        assert 1==1

    def test_fail(self):
        assert 1==2

    def test_exceptionfail(self):
        with pytest.raises(IOError):
            1 == 1

    @pytest.mark.xfail
    def test_xfail(self):
        pass