# -*- coding: utf-8 -*-
#
# Copyright © 2013 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
r"""
Reader and writer for sending stream of python objects using JSON.

These classes can be used to send Python objects (specifically, ints, floats,
strings, bools, lists, dictionaries or None) over a text stream. Partially
received objects are correctly handled.

Since multiple JSON-encoded objects cannot simply concatenated (i.e., JSON is
not a framed protocol), every object is sent over the text channel in the
format "N \n s \n", where the string s is its JSON encoding and N is the length
of s.
"""

# Standard library imports
import json

# Third party imports
from spyder.py3compat import PY2, to_text_string


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
        Write Python object to the stream and flush.

        Arguments
        ---------
        obj : object
            Object to be written. The type should be supported by JSON (i.e.,
            int, float, str, bool, list, dict or None).
        """
        txt = json.dumps(obj)
        if PY2:
            txt = to_text_string(txt)
        self.stream.write(to_text_string(len(txt)) + '\n')
        self.stream.write(txt + '\n')
        self.stream.flush()


class JSONStreamReader:
    """
    Reader for sending stream of Python objects using JSON.

    This class is used to receive a stream sent by JSONStreamWriter.

    Attributes
    ----------
    buffer : str
       Text encoding an object that has not been completely received yet.
    """

    def __init__(self):
        """Constructor."""
        self.buffer = ''

    def consume(self, txt):
        """
        Decode given text and return list of objects encoded in it.

        If only a part of the encoded text of an object is passed, then it is
        stored and combined with the remainder in the next call.
        """
        index = 0
        res = []
        txt = self.buffer + txt
        while index < len(txt):
            has_r = False  # whether line ends with \r\n or \n
            end_of_line1 = txt.find('\n', index)
            try:
                len_encoding = int(txt[index:end_of_line1])
            except ValueError:
                raise ValueError('txt = %s  index = %d  end_of_line1 = %d'
                                 % (repr(txt), index, end_of_line1))
            if end_of_line1 + len_encoding + 2 > len(txt):  # 2 for two \n
                break
            if txt[end_of_line1 + len_encoding + 1] == '\r':
                if end_of_line1 + len_encoding + 3 > len(txt):
                    break
                else:
                    has_r = True
            encoding = txt[end_of_line1 + 1:end_of_line1 + len_encoding + 1]
            res.append(json.loads(encoding))
            index = end_of_line1 + len_encoding + 2
            if has_r:
                index += 1
        self.buffer = txt[index:]
        return res
