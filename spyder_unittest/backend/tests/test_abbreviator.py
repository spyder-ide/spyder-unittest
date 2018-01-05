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
    assert abb.abbreviate('ham') == 'ham'

def test_abbreviator_with_one_word_with_two_components():
    abb = Abbreviator()
    abb.add('ham.spam')
    assert abb.abbreviate('ham.spam') == 'h.spam'

def test_abbreviator_with_one_word_with_three_components():
    abb = Abbreviator()
    abb.add('ham.spam.eggs')
    assert abb.abbreviate('ham.spam.eggs') == 'h.s.eggs'

def test_abbreviator_without_common_prefix():
    abb = Abbreviator(['ham.foo', 'spam.foo'])
    assert abb.abbreviate('ham.foo') == 'h.foo'
    assert abb.abbreviate('spam.foo') == 's.foo'

def test_abbreviator_with_prefix():
    abb = Abbreviator(['test_ham.x', 'test_spam.x'])
    assert abb.abbreviate('test_ham.x') == 'test_h.x'
    assert abb.abbreviate('test_spam.x') == 'test_s.x'

def test_abbreviator_with_first_word_prefix_of_second():
    abb = Abbreviator(['ham.x', 'hameggs.x'])
    assert abb.abbreviate('ham.x') == 'ham.x'
    assert abb.abbreviate('hameggs.x') == 'hame.x'

def test_abbreviator_with_second_word_prefix_of_first():
    abb = Abbreviator(['hameggs.x', 'ham.x'])
    assert abb.abbreviate('hameggs.x') == 'hame.x'
    assert abb.abbreviate('ham.x') == 'ham.x'

def test_abbreviator_with_three_words():
    abb = Abbreviator(['hamegg.x', 'hameggs.x', 'hall.x'])
    assert abb.abbreviate('hamegg.x') == 'hamegg.x'
    assert abb.abbreviate('hameggs.x') == 'hameggs.x'
    assert abb.abbreviate('hall.x') == 'hal.x'

def test_abbreviator_with_multilevel():
    abb = Abbreviator(['ham.eggs.foo', 'ham.spam.bar', 'eggs.ham.foo',
                       'eggs.hamspam.bar'])
    assert abb.abbreviate('ham.eggs.foo') == 'h.e.foo'
    assert abb.abbreviate('ham.spam.bar') == 'h.s.bar'
    assert abb.abbreviate('eggs.ham.foo') == 'e.ham.foo'
    assert abb.abbreviate('eggs.hamspam.bar') == 'e.hams.bar'
