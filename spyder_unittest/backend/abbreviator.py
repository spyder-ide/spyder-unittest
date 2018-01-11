# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Class for abbreviating test names."""


class Abbreviator:
    """
    Abbreviates names so that abbreviation identifies name uniquely.

    First, all names are split in components separated by full stop (like
    module names in Python). Every component is abbreviated by the smallest
    prefix not shared by other names in the same directory, except for the
    last component which is not changed.

    Attributes
    ----------
    dic : dict of (str, [str, Abbreviator])
        keys are the first-level components, values are a list, with the
        abbreviation as its first element and an Abbreviator for abbreviating
        the higher-level components as its second element.
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
        if '.' not in name:
            return
        len_abbrev = 1
        start, rest = name.split('.', 1)
        for other in self.dic:
            if start[:len_abbrev] == other[:len_abbrev]:
                if start == other:
                    break
                while (start[:len_abbrev] == other[:len_abbrev]
                       and len_abbrev < len(start)
                       and len_abbrev < len(other)):
                    len_abbrev += 1
                if len_abbrev == len(start):
                    self.dic[other][0] = other[:len_abbrev + 1]
                elif len_abbrev == len(other):
                    self.dic[other][0] = other
                    len_abbrev += 1
                else:
                    if len(self.dic[other][0]) < len_abbrev:
                        self.dic[other][0] = other[:len_abbrev]
        else:
            self.dic[start] = [start[:len_abbrev], Abbreviator()]
        self.dic[start][1].add(rest)

    def abbreviate(self, name):
        """Return abbreviation of name."""
        if '.' in name:
            start, rest = name.split('.', 1)
            res = (self.dic[start][0]
                   + '.' + self.dic[start][1].abbreviate(rest))
        else:
            res = name
        return res
