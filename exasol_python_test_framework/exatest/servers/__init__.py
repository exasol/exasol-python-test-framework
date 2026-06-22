import http.server
import socketserver
import select
import socket
import threading

from ..threading import Thread
from .. import utils

class BaseSimpleServer(object):
    def __init__(self):
        self._thread = None
        self.host = None
        self.port = None

    @property
    def address(self):
        return (self.host, self.port)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        pass

    def stop(self):
        self._thread.shutdown()
        self._thread.join(5)

class MessageBox(BaseSimpleServer):
    def _messagebox(self, s):
        slf = threading.current_thread()
        slf.data = []
        s.listen(20)
        while not slf.shutdown_requested():
            if s in select.select([s], [], [], 1)[0]:
                sock, addr = s.accept()
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
        print('host: {}, sn.host: {}, sn.port: {}'.format(self.host, s.getsockname()[0], self.port))

    @property
    def data(self):
        return self._thread.data

class EchoServer(BaseSimpleServer):
    def _echo(self, s):
        slf = threading.current_thread()
        s.listen(20)
        while not slf.shutdown_requested():
            if s in select.select([s], [], [], 1)[0]:
                sock, addr = s.accept()
                data = sock.recv(4096)
                if (data):
                    sock.send(data)
                sock.close()
        s.close()

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        self._thread = Thread(target=self._echo, args=(s,))
        self._thread.start()
        self.host = socket.gethostbyname(socket.getfqdn())
        self.port = s.getsockname()[1]

class UDPEchoServer(BaseSimpleServer):
    def _echo(self, s):
        slf = threading.current_thread()
        while not slf.shutdown_requested():
            if s in select.select([s], [], [], 1)[0]:
                data, addr = s.recvfrom(1024)
                s.sendto(data,addr)
        s.close()

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('', 0))
        self._thread = Thread(target=self._echo, args=(s,))
        self._thread.start()
        self.host = socket.gethostbyname(socket.getfqdn())
        self.port = s.getsockname()[1]

class _ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class HTTPServer(BaseSimpleServer):
    def __init__(self, documentroot='.'):
        super(HTTPServer, self).__init__()
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
        super(HTTPServer, self).stop()

from .ftp import FTPServer
from .smtp import SMTPServer

# vim: ts=4:sts=4:sw=4:et:fdm=indent
__ver__ = '1.5.4'
__author__ = "Giampaolo Rodola' <g.rodola@gmail.com>"
__web__ = 'https://github.com/giampaolo/pyftpdlib/'
