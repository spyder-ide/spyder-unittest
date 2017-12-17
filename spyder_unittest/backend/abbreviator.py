# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Class for abbreviating test names."""


class Abbreviator:
    """
    Abbreviates names so that abbreviation identifies name uniquely.

    The abbreviation is the smallest prefix not shared by other names in a
    given list.
    """

    def __init__(self, names=[]):
        """
        Constructor.

        Arguments
        ---------
        names : list of str
            list of words which needs to be abbreviated.
        """
        self.dic = {}
        for name in names:
            self.add(name)

    def add(self, name):
        """
        Add name to list of names to be abbreviated.

        Arguments
        ---------
        name : str
        """
        len_abbrev = 1
        for other in self.dic:
            if name[:len_abbrev] == other[:len_abbrev]:
                assert name != other
                while (name[:len_abbrev] == other[:len_abbrev]
                       and len_abbrev < len(name) and len_abbrev < len(other)):
                    len_abbrev += 1
                if len_abbrev == len(name):
                    self.dic[other] = other[:len_abbrev + 1]
                elif len_abbrev == len(other):
                    self.dic[other] = other
                    len_abbrev += 1
                else:
                    self.dic[other] = other[:len_abbrev]
        self.dic[name] = name[:len_abbrev]

    def abbreviate(self, name):
        """Return abbreviation of name."""
        return self.dic[name]
