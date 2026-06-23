"""Shared lightweight test servers used by the framework."""

import http.server
import select
import socket
import socketserver
import threading

from ..threading import Thread
from .. import utils


class BaseSimpleServer:
    """Base class for simple background test servers."""

    def __init__(self):
        self._thread = None
        self.host = None
        self.port = None

    @property
    def address(self):
        """Return the host/port pair for the running server."""
        return (self.host, self.port)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        """Start the server."""
        raise NotImplementedError

    def stop(self):
        """Stop the server thread."""
        self._thread.shutdown()
        self._thread.join(5)


class MessageBox(BaseSimpleServer):
    """Small server that stores received payloads."""

    def _messagebox(self, s):
        slf = threading.current_thread()
        slf.data = []
        s.listen(20)
        while not slf.shutdown_requested():
            if s in select.select([s], [], [], 1)[0]:
                sock, _addr = s.accept()
                slf.data.append(sock.recv(4096))
                sock.close()
        s.close()

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        self._thread = Thread(target=self._messagebox, args=(s,))
        self._thread.start()
        self.host = socket.gethostbyname(socket.getfqdn())
        self.port = s.getsockname()[1]

    @property
    def data(self):
        """Return the received payload list."""
        return self._thread.data


class _ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class HTTPServer(BaseSimpleServer):
    """Serve files from a temporary document root."""

    def __init__(self, documentroot='.'):
        super().__init__()
        self.documentroot = documentroot
        self._server = None

    def _httpserver(self):
        with utils.chdir(self.documentroot):
            self._server.serve_forever()

    def start(self):
        handler = http.server.SimpleHTTPRequestHandler
        self._server = _ThreadedTCPServer(('', 0), handler)

        self._thread = Thread(target=self._httpserver, args=())
        self._thread.start()
        self.host = socket.gethostbyname(socket.getfqdn())
        self.port = self._server.server_address[1]

    def stop(self):
        self._server.shutdown()
        super().stop()
