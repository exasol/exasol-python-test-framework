import argparse
import os
import socket


from inspect import cleandoc
from pathlib import Path


def validate_driver_path(arg: str):
    if not arg:
        raise argparse.ArgumentTypeError("The driver path is empty!")
    path = Path(arg).expanduser().absolute()
    if not path.exists():
        raise argparse.ArgumentTypeError(f'The driver path "{path}" does not exist!')
    else:
        return path


def validate_server(arg: str):
    if not arg:
        raise argparse.ArgumentTypeError("The connection string is empty!")
    return arg


LOG_LEVELS = {
    "off": None,
    "error": "ON ERROR ONLY",
    "normal": "DEFAULT",
    "verbose": "VERBOSE",
}

ENV_VAR = "ODBCINI"


class ClientSetup(object):

    def __init__(self):
        self.dsn = "exatest"

    def odbc_arguments(self, parser):
        parser.add_argument(
            "--server",
            help="connection string",
            required=True,
            type=validate_server)
        parser.add_argument(
            "--user", help="connection user", nargs="?", type=str, default="sys")
        parser.add_argument(
            "--password", help="connection password", nargs="?", type=str, default="exasol")
        parser.add_argument(
            "--driver",
            help="path to ODBC driver",
            required=True,
            type=validate_driver_path)
        parser.add_argument(
            "--odbc-log", choices=LOG_LEVELS,
            help="activate ODBC driver log (default: off)")
        return parser

    def _write_odbcini(self, log_path, server, driver, user,
                       password, odbc_log, fingerprint = None) -> Path:
        def cleandoc_nl(string):
            return cleandoc(string) + "\n"

        path = Path(log_path).joinpath("odbc.ini").resolve()
        server = socket.getfqdn(server)
        with path.open('w') as file:
            file.write(cleandoc_nl(
                    # TODO: Maybe make CONNECTIONLCCTYPE optional
                    f"""
                    [ODBC Data Sources]
                    {self.dsn}=EXASolution

                    [{self.dsn}]
                    Driver = {driver}
                    EXAHOST = {server}
                    EXAUID = {user}
                    EXAPWD = {password}
                    CONNECTIONLCCTYPE = en_US.UTF-8
                    CONNECTIONLCNUMERIC = en_US.UTF-8
                    SSLCERTIFICATE = SSL_VERIFY_NONE
                    """
                    ))
            if fingerprint:
                file.write(f"FINGERPRINT = {fingerprint}\n")
            if odbc_log != "off":
                file.write(cleandoc_nl(
                        f"""
                        EXALOGFILE = {log_path}/exaodbc.log
                        LOG_LEVELS = {LOG_LEVELS[odbc_log]}
                        """
                        ))
        return path

    def prepare_odbc_init(self, log_path, server, driver, user, password, odbc_log, fingerprint = None):
        path = self._write_odbcini(log_path, server, driver, user, password, odbc_log, fingerprint)
        os.environ[ENV_VAR] = path


import sys
if __name__ == "__main__":
    setup = ClientSetup()
    parser = argparse.ArgumentParser(
        description="""
        Synchronize sub-tasks from GitHub to Jira.
        """
    )
    args = setup.odbc_arguments(parser).parse_args()
    dir = Path("/home/chku/tmp")
    setup.prepare_odbc_init(
        dir,
        "localhost",
        "my-driver",
        "my-user",
        "my-password",
        "verbose",
        "fp",
    )
