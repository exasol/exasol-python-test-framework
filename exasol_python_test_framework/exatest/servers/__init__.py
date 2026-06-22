

import http.server
import socketserver
import collections
import os
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

class FTPServer(BaseSimpleServer):
    def __init__(self, documentroot='.', authorizer=None):
        from . import authorizers
        super(FTPServer, self).__init__()
        self.documentroot = documentroot
        if authorizer is None:
            self.authorizer = authorizers.DummyAuthorizer()
            self.authorizer.add_anonymous(self.documentroot)
        else:
            self.authorizer = authorizer
        self._server = None

    def _ftpserver(self):
        self._server.serve_forever(poll_interval=1)

    def _create_server(self):
        if self._server is None:
            self._server = _FTPControlServer(
                ('', 0),
                documentroot=self.documentroot,
                authorizer=self.authorizer,
                host_ip=socket.gethostbyname(socket.getfqdn()),
            )
            self.host = socket.gethostbyname(socket.getfqdn())
            self.port = self._server.server_address[1]

    def start(self):
        self._create_server()
        self._thread = Thread(target=self._ftpserver, args=())
        self._thread.start()

    def serve_forever(self):
        self._create_server()
        self._server.serve_forever(poll_interval=1)

    def stop(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            super(FTPServer, self).stop()

    def close_all(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()


class _FTPDataListener:
    def __init__(self, host_ip):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((host_ip, 0))
        self._socket.listen(1)

    @property
    def address(self):
        return self._socket.getsockname()

    def accept(self):
        return self._socket.accept()

    def close(self):
        self._socket.close()


class _FTPControlHandler(socketserver.StreamRequestHandler):
    def setup(self):
        super().setup()
        self.username = None
        self.authenticated = False
        self.home = self.server.documentroot
        self.cwd = "/"
        self._data_listener = None

    def finish(self):
        self._close_data_listener()
        super().finish()

    def _send(self, code, message):
        self.wfile.write(f"{code} {message}\r\n".encode("ascii"))

    def _close_data_listener(self):
        if self._data_listener is not None:
            self._data_listener.close()
            self._data_listener = None

    def _path_to_real(self, path):
        if not path or path == ".":
            rel = self.cwd.lstrip("/")
        elif os.path.isabs(path):
            rel = path.lstrip("/")
        else:
            rel = os.path.join(self.cwd.lstrip("/"), path)
        real = os.path.normpath(os.path.join(self.home, rel))
        home = os.path.normpath(self.home)
        if os.path.commonpath([home, real]) != home:
            raise ValueError("path escapes user home directory")
        return real

    def _path_to_ftp(self, path):
        home = os.path.normpath(self.home)
        real = os.path.normpath(path)
        if not real.startswith(home):
            return "/"
        rel = real[len(home):].replace(os.sep, "/")
        return rel if rel.startswith("/") else "/" + rel

    def _parse_host_port(self, argument):
        start = argument.find("(")
        end = argument.find(")", start + 1)
        if start == -1 or end == -1:
            raise ValueError("invalid PASV response")
        values = [int(value) for value in argument[start + 1:end].split(",")]
        if len(values) != 6:
            raise ValueError("invalid PASV response")
        return "%d.%d.%d.%d" % tuple(values[:4]), values[4] * 256 + values[5]

    def _open_passive_data_socket(self):
        self._close_data_listener()
        self._data_listener = _FTPDataListener(self.server.host_ip)
        host, port = self._data_listener.address
        octets = host.split(".")
        p1, p2 = divmod(port, 256)
        return ",".join(octets + [str(p1), str(p2)])

    def _accept_data_connection(self):
        if self._data_listener is None:
            return None
        conn, _ = self._data_listener.accept()
        self._close_data_listener()
        return conn

    def _require_login(self):
        if not self.authenticated:
            self._send(530, "Please login with USER and PASS.")
            return False
        return True

    def _check_perm(self, perm, path=None):
        if not self.server.authorizer.has_perm(self.username, perm, path):
            self._send(550, "Permission denied.")
            return False
        return True

    def _format_listing(self, directory):
        entries = []
        for name in sorted(os.listdir(directory)):
            entries.append(name)
        return "\r\n".join(entries) + ("\r\n" if entries else "")

    def handle(self):
        self._send(220, "Exasol FTP server ready")
        while True:
            raw = self.rfile.readline()
            if not raw:
                break

            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if not line:
                continue
            command, _, argument = line.partition(" ")
            command = command.upper()
            argument = argument.strip()

            if command == "USER":
                self.username = argument or "anonymous"
                self._send(331, "User name okay, need password.")
            elif command == "PASS":
                try:
                    self.server.authorizer.validate_authentication(
                        self.username or "anonymous", argument, self
                    )
                except Exception:
                    self._send(530, "Authentication failed.")
                else:
                    self.authenticated = True
                    self.home = self.server.authorizer.get_home_dir(self.username)
                    self.cwd = "/"
                    self._send(230, self.server.authorizer.get_msg_login(self.username))
            elif command == "SYST":
                self._send(215, "UNIX Type: L8")
            elif command == "FEAT":
                self.wfile.write(b"211-Features\r\n211 End\r\n")
            elif command == "PWD":
                self._send(257, f'"{self.cwd}" is current directory.')
            elif command == "TYPE":
                self._send(200, "Type set to A.")
            elif command == "NOOP":
                self._send(200, "OK")
            elif command == "QUIT":
                self._send(221, "Goodbye.")
                break
            elif command == "PASV":
                try:
                    host_port = self._open_passive_data_socket()
                except OSError:
                    self._send(425, "Can't open passive connection.")
                else:
                    self._send(227, f"Entering Passive Mode ({host_port}).")
            elif command == "LIST":
                if not self._require_login():
                    continue
                if not self._check_perm("l"):
                    continue
                try:
                    data_conn = self._accept_data_connection()
                    if data_conn is None:
                        self._send(425, "Use PASV first.")
                        continue
                    self._send(150, "Opening data connection.")
                    directory = self._path_to_real(argument or self.cwd)
                    listing = self._format_listing(directory)
                    data_conn.sendall(listing.encode("utf-8"))
                    data_conn.close()
                    self._send(226, "Transfer complete.")
                except Exception:
                    self._send(550, "Failed to list directory.")
            elif command == "MKD":
                if not self._require_login():
                    continue
                try:
                    real_path = self._path_to_real(argument)
                except ValueError:
                    self._send(550, "Invalid directory.")
                    continue
                if not self._check_perm("m", real_path):
                    continue
                try:
                    os.makedirs(real_path, exist_ok=False)
                except FileExistsError:
                    self._send(550, "Directory already exists.")
                else:
                    self._send(257, f'"{argument}" directory created.')
            elif command == "CWD":
                if not self._require_login():
                    continue
                try:
                    real_path = self._path_to_real(argument)
                except ValueError:
                    self._send(550, "Invalid directory.")
                    continue
                if not os.path.isdir(real_path):
                    self._send(550, "Directory not found.")
                    continue
                if not self._check_perm("e", real_path):
                    continue
                self.cwd = self._path_to_ftp(real_path)
                self._send(250, "Directory successfully changed.")
            else:
                self._send(502, "Command not implemented.")


class _FTPControlServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, documentroot, authorizer, host_ip):
        self.documentroot = documentroot
        self.authorizer = authorizer
        self.host_ip = host_ip
        super().__init__(server_address, _FTPControlHandler)


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

# vim: ts=4:sts=4:sw=4:et:fdm=indent
__ver__ = '1.5.4'
__author__ = "Giampaolo Rodola' <g.rodola@gmail.com>"
__web__ = 'https://github.com/giampaolo/pyftpdlib/'
