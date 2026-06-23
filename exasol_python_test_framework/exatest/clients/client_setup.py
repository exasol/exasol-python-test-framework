"""Exatest client setup helpers."""
# pylint: disable=C0114,C0115,C0116,C0301,C0303,C0305,C0411,C0103,C0209,C0204,C0415,R1705,R1710,R1720,R1732,R0205,R0903,R0911,R0912,R0913,R0917,R1725,W0201,W0212,W0231,W0238,W0511,W0603,W0611,W0612,W0622,W0702,W0718,W0719,W1201,W1202,W1514,I1101

import argparse
import os
import socket

from inspect import cleandoc
from pathlib import Path


ENV_VAR = "ODBCINI"

LOG_LEVELS = {
    "off": None,
    "error": "ON ERROR ONLY",
    "normal": "DEFAULT",
    "verbose": "VERBOSE",
}

TLS_CERT_OPTIONS = {
    "verify": None,
    "unverified": "SSL_VERIFY_NONE",
}


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
            help='activate ODBC driver log (default: %(default)s)',
        )
        parser.add_argument(
            "--tls-cert", choices=TLS_CERT_OPTIONS,
            help='TLS certificate verification (default: %(default)s)',
        )
        return parser

    def _write_odbcini(self, log_path, server, driver,
                       user, password, odbc_log,
                       tls_cert) -> str:
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
                    """
            ))
            if tls_cert != "verify":
                file.write(f"SSLCERTIFICATE = {TLS_CERT_OPTIONS[tls_cert]}\n")
            if odbc_log != "off":
                file.write(cleandoc_nl(
                        f"""
                        EXALOGFILE = {log_path}/exaodbc.log
                        LOG_LEVELS = {LOG_LEVELS[odbc_log]}
                        """
                        ))
        return str(path)

    def prepare_odbc_init(
            self,
            log_path,
            server,
            driver,
            user,
            password,
            odbc_log,
            tls_cert = "unverified",
    ):
        path = self._write_odbcini(
            log_path,
            server,
            driver,
            user,
            password,
            odbc_log,
            tls_cert,
        )
        os.environ[ENV_VAR] = path
