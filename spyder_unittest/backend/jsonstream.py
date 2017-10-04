# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""Reader and writer for sending stream of python objects using JSON."""

# Standard library imports
import json


class JSONStreamWriter:
    """
    Writer for sending stream of python objects using JSON.

    This class can be used to send a stream of python objects over a text
    stream using JSON. It is the responsibility of the caller to open and
    close the stream.

    Attributes
    ----------
    stream : TextIOBase
        text stream that the objects are sent over.
    """

    def __init__(self, stream):
        """Constructor."""
        self.stream = stream

    def write(self, obj):
        """
        Write Python object to the stream.

        Arguments
        ---------
        obj : object
            Object to be written. The type should be supported by JSON (i.e.,
            int, float, str, bool, list, dict or None).
        """
        txt = json.dumps(obj)
        self.stream.write(str(len(txt)) + '\n')
        self.stream.write(txt + '\n')
