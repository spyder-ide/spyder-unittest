# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Example tests used to generate screenshots."""

import pytest

def test_one_plus_one_is_two():
    assert 1 + 1 == 2

def test_two_plus_two_is_four():
    assert 2 + 2 == 4

def test_one_plus_two_is_five():
    assert 1 + 2 == 5

def test_two_times_two_is_four():
    assert 2 * 2 == 4

@pytest.mark.skip
def test_will_be_skipped():
    assert 0 == 1
