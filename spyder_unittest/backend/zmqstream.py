# -*- coding: utf-8 -*-
#
# Copyright © 2018 Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Reader and writer for sending stream of python objects over a ZMQ socket.

The intended usage is that you construct a reader in one process and a writer
(with the same port number as the reader) in a worker process. The worker
process can then use the stream to send its result to the reader.
"""

from __future__ import print_function

# Standard library imports
import sys

# Third party imports
from qtpy.QtCore import QObject, QProcess, QSocketNotifier, Signal
from qtpy.QtWidgets import QApplication
import zmq


class ZmqStreamWriter:
    """Writer for sending stream of Python object over a ZMQ stream."""

    def __init__(self, port):
        """
        Constructor.

        Arguments
        ---------
        port : int
            TCP port number to be used for the stream. This should equal the
            `port` attribute of the corresponding `ZmqStreamReader`.
        """
        context = zmq.Context()
        self.socket = context.socket(zmq.PAIR)
        self.socket.connect('tcp://localhost:{}'.format(port))

    def write(self, obj):
        """Write arbitrary Python object to stream."""
        self.socket.send_pyobj(obj)

    def close(self):
        """Close stream."""
        self.socket.close()


class ZmqStreamReader(QObject):
    """
    Reader for receiving stream of Python objects via a ZMQ stream.

    Attributes
    ----------
    port : int
        TCP port number used for the stream.

    Signals
    -------
    sig_received(list)
        Emitted when objects are received; argument is list of received
        objects.
    """

    sig_received = Signal(object)

    def __init__(self):
        """Constructor; also constructs ZMQ stream."""
        super(QObject, self).__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.port = self.socket.bind_to_random_port('tcp://*')
        fid = self.socket.getsockopt(zmq.FD)
        self.notifier = QSocketNotifier(fid, QSocketNotifier.Read, self)
        self.notifier.activated.connect(self.received_message)

    def received_message(self):
        """Called when a message is received."""
        self.notifier.setEnabled(False)
        messages = []
        try:
            while 1:
                message = self.socket.recv_pyobj(flags=zmq.NOBLOCK)
                messages.append(message)
        except zmq.ZMQError:
            pass
        finally:
            self.notifier.setEnabled(True)
        if messages:
            self.sig_received.emit(messages)

    def close(self):
        """Read any remaining messages and close stream."""
        self.received_message()  # Flush remaining messages
        self.notifier.setEnabled(False)
        self.socket.close()
        self.context.destroy()


if __name__ == '__main__':
    # For testing, construct a ZMQ stream between two processes and send
    # the number 42 over the stream
    if len(sys.argv) == 1:
        app = QApplication(sys.argv)
        manager = ZmqStreamReader()
        manager.sig_received.connect(print)
        process = QProcess()
        process.start('python', [sys.argv[0], str(manager.port)])
        process.finished.connect(app.quit)
        sys.exit(app.exec_())
    else:
        worker = ZmqStreamWriter(sys.argv[1])
        worker.write(42)
