# -*- coding: utf-8 -*-
#
# Copyright © 2017 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Class for abbreviating test names."""

from __future__ import annotations

# Standard imports
from dataclasses import dataclass

@dataclass
class Abbreviation:
    """
    Abbreviation for one component of a test name.

    Abbreviations are defined recursively, so `.head` is the abbreviation
    for the first component and `.tail` specifies the abbreviations for the
    second and later components.
    """
    head: str
    tail: Abbreviator


class Abbreviator:
    """
    Abbreviates names so that abbreviation identifies name uniquely.

    First, if the name contains brackets, the part in brackets starting at
    the first bracket is removed from the name. Then, all names are split
    in components separated by full stops (like module names in Python).
    Every component is abbreviated by the smallest prefix not shared by
    other names in the same directory, except for the last component which
    is not changed. Finally, the part in brackets, which was removed at the
    beginning, is appended to the abbreviated name.

    Attributes
    ----------
    dic : dict of (str, [str, Abbreviator])
        keys are the first-level components, values are a list, with the
        abbreviation as its first element and an Abbreviator for abbreviating
        the higher-level components as its second element.
    """

    def __init__(self, names: list[str]=[]) -> None:
        """
        Constructor.

        Arguments
        ---------
        names : list of str
            list of words which needs to be abbreviated.
        """
        self.dic: dict[str, Abbreviation] = {}
        for name in names:
            self.add(name)

    def add(self, name: str) -> None:
        """
        Add name to list of names to be abbreviated.

        Arguments
        ---------
        name : str
        """
        name = name.split('[', 1)[0]
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
                    self.dic[other].head = other[:len_abbrev + 1]
                elif len_abbrev == len(other):
                    self.dic[other].head = other
                    len_abbrev += 1
                else:
                    if len(self.dic[other].head) < len_abbrev:
                        self.dic[other].head = other[:len_abbrev]
        else:
            self.dic[start] = Abbreviation(start[:len_abbrev], Abbreviator())
        self.dic[start].tail.add(rest)

    def abbreviate(self, name: str) -> str:
        """Return abbreviation of name."""
        if '[' in name:
            name, parameters = name.split('[', 1)
            parameters = '[' + parameters
        else:
            parameters = ''
        if '.' in name:
            start, rest = name.split('.', 1)
            res = (self.dic[start].head
                   + '.' + self.dic[start].tail.abbreviate(rest))
        else:
            res = name
        return res + parameters
