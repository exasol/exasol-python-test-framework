"""Exatest ODBC client helpers."""
# pylint: disable=C0114,C0115,C0116,C0301,C0303,C0305,C0411,C0103,C0209,C0204,C0415,R1705,R1710,R1720,R1732,R0205,R0903,R0911,R0912,R0913,R0917,R1725,W0201,W0212,W0231,W0238,W0511,W0603,W0611,W0612,W0622,W0702,W0718,W0719,W1201,W1202,W1514,I1101

import sys
import pyodbc


class ClientError(Exception):
    pass


def getScriptLanguagesFromArgs():
    for i, arg in enumerate(sys.argv):
        if arg == '--script-languages':
            if len(sys.argv) == i + 1:
                raise ClientError('Value for --script-languages missing')
            return sys.argv[i + 1]


class ODBCClient(object):
    def __init__(self, dsn, user="sys", password="exasol"):
        self.cursor = None
        self.params = {'dsn': dsn, 'uid': user, 'pwd': password}

    def connect(self, **kwargs):
        params = self.params.copy()
        params.update(kwargs)
        self.conn = pyodbc.connect(**params, ansi=True)
        self.conn.setencoding(encoding='utf-8')
        self.cursor = self.conn.cursor()
        self._setScriptLanguagesFromArgs()

    def _setScriptLanguagesFromArgs(self):
        langs = getScriptLanguagesFromArgs()
        if langs is not None:
            self.query("ALTER SESSION SET SCRIPT_LANGUAGES='%s'" % langs)

    def query(self, qtext, *args):
        if self.cursor is None:
            raise ClientError('query() requires connect() first')
        q = self.cursor.execute(qtext, *args)
        try:
            return q.fetchall()
        except pyodbc.ProgrammingError as e:
            if 'No results.  Previous SQL was not a query.' in str(e):
                return None
            else:
                raise

    def executeStatement(self, qtext, *args):
        if self.cursor is None:
            raise ClientError('executeStatement() requires connect() first')
        self.cursor.execute(qtext, *args)
        return self.cursor.rowcount

    def columns(self, table=None, catalog=None, schema=None, column=None):
        args = {}
        if table:
            args['table'] = table
        if catalog:
            args['catalog'] = catalog
        if schema:
            args['schema'] = schema
        if column:
            args['column'] = column
        return self.cursor.columns(**args).fetchall()

    def rowcount(self):
        return self.cursor.rowcount

    def cursorDescription(self):
        return self.cursor.description

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.cursor.close()
        self.conn.close()

# vim: ts=4:sts=4:sw=4:et:fdm=indent
