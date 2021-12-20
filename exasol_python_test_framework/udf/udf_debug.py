import asynchat
import asyncore
import io
import socket
import sys
import threading
import time
import traceback
from multiprocessing import Process, Queue
from queue import Full
from threading import Thread
from typing import Optional, Tuple

from exasol_python_test_framework import udf


class LogServer(asyncore.dispatcher):
    def __init__(self, server_address: Tuple[str, int], output: Queue):
        output.put_nowait(f"Server address:{server_address}\n")
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = server_address
        self.output = output

        self.bind(self.server_address)

        if self.server_address[1] == 0:
            self.server_address = (self.server_address[0], self.socket.getsockname()[1])
        self.listen(10)

    def handle_accept(self):
        conn, addr = self.accept()
        LogHandler(conn, addr, self.output)

    def handle_close(self):
        self.close()


class LogHandler(asynchat.async_chat):
    def __init__(self, sock, address: Tuple, output: Queue):
        asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator("\n")
        self.address = "%s:%d" % address
        self.output = output
        self.ibuffer = []

    def collect_incoming_data(self, data):
        self.ibuffer.append(data)

    def found_terminator(self):
        try:
            self.output.put_nowait("%s> %s\n" % (self.address, ''.join(self.ibuffer).rstrip()))
        except Full as full_ex:
            print(f"Queue is full for UDF debug:{full_ex}", file=sys.stderr)
        self.ibuffer = []


class ScriptOutputThread(Thread):

    def __init__(self, server_address: Tuple[str, int], output: Queue):
        super().__init__()
        self.server_address = server_address
        self.server = LogServer(server_address, output)
        self.finished = False

    def run(self):
        try:
            while True:
                asyncore.loop(timeout=1, count=1)
        finally:
            self.server.close()
            del self.server
            asyncore.close_all()


def output_service(queue: Queue, server: Optional[str], port: Optional[int]):
    """Start a standalone output service

    This service can be used in an other Python or R instance, for
    Python instances the connection parameter externalClient need to
    be specified.
    """
    try:
        host = socket.gethostbyname(socket.gethostname())
    except:
        host = '0.0.0.0'

    if server is None:
        server = host
    if port is None:
        port = 3000

    address = server, port

    server = ScriptOutputThread(server_address=address, output=queue)
    queue.put_nowait(f">>> bind the output server to {server}:{port}")
    try:
        server.run()
    except KeyboardInterrupt:
        sys.stdout.flush()


def start_udf_output_redirect_consumer(test_case: udf.TestCase, output: io.TextIOBase):
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print("local_ip", local_ip)

    queue = Queue()
    process = Process(target=output_service, args=(queue, None, None))
    process.start()

    def print_stdout():
        while process.is_alive():
            try:
                msg = queue.get()
                output.write(f"UDF DEBUG {msg}\n")
            except:
                traceback.print_exc()
                pass
        queue.close()

    stdout_thread = threading.Thread(target=print_stdout)
    stdout_thread.start()
    time.sleep(10)
    if process.is_alive():
        test_case.query("ALTER SESSION SET SCRIPT_OUTPUT_ADDRESS='%s:3000';" % local_ip)
        return process, queue
    else:
        if not queue.empty():
            print(f"UDF debug std output '{queue.get_nowait()}'")
        queue.put("Cancel") # Send message to cancel stdout_thread
        test_case.fail("Could not start udf_debug.py")


class UdfDebugger:
    def __init__(self, test_case: udf.TestCase, output: io.TextIOBase = sys.stdout):
        self.output = output
        self.test_case = test_case

    def __enter__(self):
        self._process, self._queue = start_udf_output_redirect_consumer(self.test_case, self.output)

    def __exit__(self, type_, value, traceback):
        if self._process is not None:
            # Wait 1s to give socket time to process all remaining messages
            time.sleep(1)
            self._process.terminate()
            print("Calling terminate")
            self._queue.put("Completed")

        self._process = None
        self._queue = None
