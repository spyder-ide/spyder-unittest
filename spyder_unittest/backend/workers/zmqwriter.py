# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Writer for sending stream of python objects over a ZMQ socket.

The intended usage is that you construct a ZmqStreamReader in one process
and a ZmqStreamWriter (with the same port number as the reader) in a worker
process. The worker process can then use the stream to send its result to the
reader.
"""

# Standard library imports
import sys

# Third party imports
import zmq


class ZmqStreamWriter:
    """Writer for sending stream of Python object over a ZMQ stream."""

    def __init__(self, port: str) -> None:
        """
        Constructor.

        Arguments
        ---------
        port : str
            TCP port number to be used for the stream. This should equal the
            `port` attribute of the corresponding `ZmqStreamReader`.
        """
        context = zmq.Context()
        self.socket = context.socket(zmq.PAIR)
        self.socket.connect('tcp://localhost:{}'.format(port))

    def write(self, obj: object) -> None:
        """Write arbitrary Python object to stream."""
        self.socket.send_pyobj(obj)

    def close(self) -> None:
        """Close stream."""
        self.socket.close()


class FileStub(ZmqStreamWriter):
    """Stub for ZmqStreamWriter which instead writes to a file."""

    def __init__(self, filename: str) -> None:
        """Constructor; connect to specified filename."""
        self.file = open(filename, 'w')

    def write(self, obj: object) -> None:
        """Write Python object to file."""
        self.file.write(str(obj) + '\n')

    def close(self) -> None:
        """Close file."""
        self.file.close()


if __name__ == '__main__':
    # Usage: python zmqwriter.py <port>
    # Construct a ZMQ stream on the given port number and send the number 42
    # over the stream (for testing)
    worker = ZmqStreamWriter(sys.argv[1])
    worker.write(42)
