import collections
import socket
import socketserver

from ..threading import Thread
from . import BaseSimpleServer


class _SMTPMessageHandler(socketserver.StreamRequestHandler):
    _message = collections.namedtuple("Message", "host, sender, recipients, body")

    def _write(self, text):
        self.wfile.write((text + "\r\n").encode("ascii"))

    @staticmethod
    def _extract_address(argument):
        value = argument.strip()
        if ":" in value:
            value = value.split(":", 1)[1].strip()
        if " " in value:
            value = value.split(" ", 1)[0]
        return value.strip("<>")

    def _debug_message(self, peer, sender, recipients, body):
        if not self.server.debug:
            return
        print("---------- MESSAGE ENVELOPE ---------")
        print("Peer:", peer)
        print("From:", sender)
        print("To:", ", ".join(recipients))
        print("---------- MESSAGE FOLLOWS ----------")
        for index, line in enumerate(body.split(b"\r\n")):
            if index == 0 and not line:
                print("X-Peer:", peer[0])
            print(line)
        print("------------ END MESSAGE ------------")

    def handle(self):
        self._write("220 localhost Exasol SMTP server ready")
        sender = None
        recipients = []
        in_data = False
        data_lines = []

        while True:
            raw = self.rfile.readline()
            if not raw:
                break

            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            command = line.split(" ", 1)[0].upper()
            argument = line[len(command):].strip()

            if in_data:
                if line == ".":
                    body = "\r\n".join(data_lines).encode("utf-8")
                    self.server.messages.append(
                        self._message(self.client_address, sender, recipients, body)
                    )
                    self._debug_message(self.client_address, sender, recipients, body)
                    in_data = False
                    data_lines = []
                    self._write("250 OK")
                else:
                    data_lines.append(line)
                continue

            if command == "EHLO":
                self._write("250-localhost")
                self._write("250-SIZE 33554432")
                self._write("250-8BITMIME")
                self._write("250 HELP")
            elif command == "HELO":
                self._write("250 localhost")
            elif command == "MAIL":
                sender = self._extract_address(argument)
                recipients = []
                self._write("250 OK")
            elif command == "RCPT":
                recipients.append(self._extract_address(argument))
                self._write("250 OK")
            elif command == "DATA":
                in_data = True
                data_lines = []
                self._write("354 End data with <CR><LF>.<CR><LF>")
            elif command == "RSET":
                sender = None
                recipients = []
                data_lines = []
                in_data = False
                self._write("250 OK")
            elif command == "NOOP":
                self._write("250 OK")
            elif command == "QUIT":
                self._write("221 Bye")
                break
            else:
                self._write("502 Command not implemented")


class _SMTPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, debug=False):
        self.debug = debug
        self.messages = []
        super().__init__(server_address, _SMTPMessageHandler)


class SMTPServer(BaseSimpleServer):
    def __init__(self, debug=False):
        super(SMTPServer, self).__init__()
        self.debug = debug
        self._server = None

    def _smtpserver(self):
        self._server.serve_forever(poll_interval=1)

    def start(self):
        self._server = _SMTPServer(('', 0), debug=self.debug)
        self._thread = Thread(target=self._smtpserver, args=())
        self._thread.start()
        self.host = socket.gethostbyname(socket.getfqdn())
        self.port = self._server.server_address[1]

    def stop(self):
        self._server.shutdown()
        self._server.server_close()
        super(SMTPServer, self).stop()

    @property
    def messages(self):
        return self._server.messages
