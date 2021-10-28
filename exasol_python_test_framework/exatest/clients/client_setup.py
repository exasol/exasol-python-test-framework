import argparse
import os
import socket


def validate_driver_path(arg: str):
    if not arg:
        raise argparse.ArgumentTypeError("The driver path is empty!")
    import os.path
    absolute = os.path.abspath(os.path.expanduser(arg))
    if not os.path.exists(absolute):
        raise argparse.ArgumentTypeError(f"The driver path '{absolute}' does not exist!")
    else:
        return absolute


def validate_server(arg: str):
    if not arg:
        raise argparse.ArgumentTypeError("The connection string is empty!")
    return arg


class ClientSetup(object):

    def __init__(self):
        self.dsn = "exatest"

    def odbc_arguments(self, arg_parser):
        arg_parser.add_argument('--server',
                          help='connection string',
                          required=True,
                          type=lambda x: validate_server(x))
        arg_parser.add_argument('--user', help='connection user', nargs="?", type=str, default="sys")
        arg_parser.add_argument('--password', help='connection password', nargs="?", type=str, default="exasol")
        arg_parser.add_argument('--driver',
                          help='path to ODBC driver',
                          required=True,
                          type=lambda x: validate_driver_path(x))
        odbcloglevel = ('off', 'error', 'normal', 'verbose')
        arg_parser.add_argument('--odbc-log', choices=odbcloglevel,
                          help='activate ODBC driver log (default: %(default)s)')

        return arg_parser

    def _write_odbcini(self, log_path, server, driver, user, password, odbc_log):
        name = os.path.realpath(os.path.join(log_path, 'odbc.ini'))
        server=socket.getfqdn(server)
        with open(name, 'w') as tmp:
            tmp.write('[ODBC Data Sources]\n')
            tmp.write('%s=EXASolution\n'%self.dsn)
            tmp.write('\n')
            tmp.write('[%s]\n'%self.dsn)
            tmp.write('Driver = %s\n' % driver)
            tmp.write('EXAHOST = %s\n' % server)
            tmp.write('EXAUID = %s\n' % user)
            tmp.write('EXAPWD = %s\n' % password)
            tmp.write('CONNECTIONLCCTYPE = en_US.UTF-8\n')      # TODO Maybe make this optional
            tmp.write('CONNECTIONLCNUMERIC = en_US.UTF-8\n')
            if odbc_log != 'off':
                tmp.write('EXALOGFILE = %s/exaodbc.log\n' % log_path.logdir)
                tmp.write('LOGMODE = %s\n' % {
                        'error': 'ON ERROR ONLY',
                        'normal': 'DEFAULT',
                        'verbose': 'VERBOSE',
                        }[odbc_log])
        return name

    def prepare_odbc_init(self, log_path, server, driver, user, password, odbc_log):
        name = self._write_odbcini(log_path, server, driver, user, password, odbc_log)
        os.environ['ODBCINI'] = name
