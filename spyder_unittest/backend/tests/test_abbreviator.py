# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Tests for abbreviator.py"""

# Local imports
from spyder_unittest.backend.abbreviator import Abbreviator


def test_abbreviator_with_one_word():
    abb = Abbreviator()
    abb.add('ham')
    assert abb.abbreviate('ham') == 'h'

def test_abbreviator_without_common_prefix():
    abb = Abbreviator(['ham', 'spam'])
    assert abb.abbreviate('ham') == 'h'
    assert abb.abbreviate('spam') == 's'

def test_abbreviator_with_prefix():
    abb = Abbreviator(['test_ham', 'test_spam'])
    assert abb.abbreviate('test_ham') == 'test_h'
    assert abb.abbreviate('test_spam') == 'test_s'

def test_abbreviator_with_first_word_prefix_of_second():
    abb = Abbreviator(['ham', 'hameggs'])
    assert abb.abbreviate('ham') == 'ham'
    assert abb.abbreviate('hameggs') == 'hame'

def test_abbreviator_with_second_word_prefix_of_first():
    abb = Abbreviator(['hameggs', 'ham'])
    assert abb.abbreviate('hameggs') == 'hame'
    assert abb.abbreviate('ham') == 'ham'

def test_abbreviator_with_multilevel():
    abb = Abbreviator(['ham.eggs', 'ham.spam', 'eggs.ham', 'eggs.hamspam'])
    assert abb.abbreviate('ham.eggs') == 'h.e'
    assert abb.abbreviate('ham.spam') == 'h.s'
    assert abb.abbreviate('eggs.ham') == 'e.ham'
    assert abb.abbreviate('eggs.hamspam') == 'e.hams'
