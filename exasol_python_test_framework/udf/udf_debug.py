"""Helpers for capturing UDF process output during integration tests."""

import io
import socket
import socketserver
import sys
import threading
import time
import traceback
from multiprocessing import Process, Queue
from queue import Full
from threading import Thread
from typing import Optional, Tuple

from exasol_python_test_framework import docker_db_environment, udf


class LogHandler(socketserver.StreamRequestHandler):
    """Read output lines from the UDF log socket."""

    def handle(self):
        address = f"{self.client_address[0]}:{self.client_address[1]}"
        buffer = []
        while True:
            data = self.rfile.readline()
            if not data:
                break
            buffer.append(data.decode("utf-8", "replace").rstrip("\r\n"))
            if data.endswith(b"\n"):
                message = f"{address}> {''.join(buffer).rstrip()}\n"
                try:
                    self.server.output.put_nowait(message)
                except Full as full_ex:
                    print(f"Queue is full for UDF debug:{full_ex}", file=sys.stderr)
                buffer = []


class LogServer(socketserver.ThreadingTCPServer):
    """Background socket server that forwards messages into a queue."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address: Tuple[str, int], output: Queue):
        output.put_nowait(f"Server address:{server_address}\n")
        self.output = output
        super().__init__(server_address, LogHandler)


class ScriptOutputThread(Thread):
    """Serve UDF output in a background thread."""

    def __init__(self, server_address: Tuple[str, int], output: Queue):
        super().__init__()
        self.server_address = server_address
        self.server = LogServer(server_address, output)
        self.finished = False

    def run(self):
        try:
            self.server.serve_forever(poll_interval=1)
        finally:
            self.server.shutdown()
            self.server.server_close()
            del self.server


def output_service(queue: Queue, server: Optional[str], port: Optional[int]):
    """Start a standalone output service.

    This service can be used in another Python or R instance, for
    Python instances the connection parameter externalClient need to
    be specified.
    """
    try:
        host = socket.gethostbyname(socket.gethostname())
    except OSError:
        host = "0.0.0.0"

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


def start_udf_output_redirect_consumer(
    test_case: udf.TestCase, server: Optional[str], output: io.TextIOBase
):
    """Start the output forwarding process and its consumer thread."""

    if server is None:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    else:
        local_ip = server
    print("local_ip", local_ip)

    port = 3000

    queue = Queue()
    process = Process(target=output_service, args=(queue, local_ip, port))
    process.start()

    def print_stdout():
        t = threading.current_thread()
        while getattr(t, "keep_going", True):
            try:
                msg = queue.get()
                output.write(f"UDF DEBUG {msg}\n")
            except (OSError, ValueError):
                traceback.print_exc()
        queue.close()

    stdout_thread = threading.Thread(target=print_stdout)
    stdout_thread.start()
    time.sleep(10)
    if process.is_alive():
        test_case.query(f"ALTER SESSION SET SCRIPT_OUTPUT_ADDRESS='{local_ip}:{port}';")
        return process, queue, stdout_thread
    stdout_thread.keep_going = False
    queue.put("Cancel")  # Send message to cancel stdout_thread
    test_case.fail("Could not start udf_debug.py")
    return None, None, None


class UdfDebugger:
    """Context manager for temporary UDF output redirection."""

    def __init__(
        self,
        test_case: udf.TestCase,
        server: Optional[str] = None,
        output: Optional[io.TextIOBase] = sys.stdout,
    ):
        self.output = output
        self.test_case = test_case
        self.server = server
        self._process = None
        self._queue = None
        self._stdout_thread = None

    def __enter__(self):
        return self._activate()

    def start(self):
        """Enter the debugger context explicitly."""
        return self._activate()

    def _activate(self):
        self._process, self._queue, self._stdout_thread = (
            start_udf_output_redirect_consumer(
                test_case=self.test_case, server=self.server, output=self.output
            )
        )
        return self

    def __exit__(self, type_, value, trace_back):
        if self._process is not None:
            self._process.terminate()
            # Wait 1s to give socket time to process all remaining messages
            self._stdout_thread.keep_going = False
            self._queue.put("Completed")

        self._process = None
        self._queue = None

    def stop(self, type_=None, value=None, trace_back=None):
        """Exit the debugger context explicitly."""
        return self.__exit__(type_, value, trace_back)


class UdfDebuggerFromDockerHost(UdfDebugger):
    """UdfDebugger configured with the Docker host IP."""

    def __init__(
        self, test_case: udf.TestCase, output: Optional[io.TextIOBase] = sys.stdout
    ):
        env = docker_db_environment.DockerDBEnvironment("")
        super().__init__(
            test_case=test_case,
            server=env.get_ip_address_of_host(),
            output=output,
        )
