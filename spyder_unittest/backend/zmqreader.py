# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
"""
Reader for sending stream of python objects over a ZMQ socket.

The intended usage is that you construct a ZmqStreamReader in one process
and a ZmqStreamWriter (with the same port number as the reader) in a worker
process. The worker process can then use the stream to send its result to the
reader.
"""

# Third party imports
from qtpy.QtCore import QObject, QProcess, QSocketNotifier, Signal
from qtpy.QtWidgets import QApplication
import zmq


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

    def __init__(self) -> None:
        """Constructor; also constructs ZMQ stream."""
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.port = self.socket.bind_to_random_port('tcp://*')
        fid = self.socket.getsockopt(zmq.FD)
        self.notifier = QSocketNotifier(fid, QSocketNotifier.Read, self)
        self.notifier.activated.connect(self.received_message)

    def received_message(self) -> None:
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

    def close(self) -> None:
        """Read any remaining messages and close stream."""
        self.received_message()  # Flush remaining messages
        self.notifier.setEnabled(False)
        self.socket.close()
        self.context.destroy()


if __name__ == '__main__':
    # Usage: python zmqreader.py
    # Start zmqwriter.py in another process and construct a ZMQ stream between
    # this process and the zmqwriter process. Read and print what zmqwriter
    # sends over the ZMQ stream.

    import os.path
    import sys

    app = QApplication(sys.argv)
    manager = ZmqStreamReader()
    manager.sig_received.connect(print)
    process = QProcess()
    dirname = os.path.dirname(sys.argv[0])
    writer_name = os.path.join(dirname, 'workers', 'zmqwriter.py')
    process.start('python', [writer_name, str(manager.port)])
    process.finished.connect(app.quit)
    sys.exit(app.exec_())
