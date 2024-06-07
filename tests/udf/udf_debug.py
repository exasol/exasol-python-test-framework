import io
from datetime import date, datetime
from decimal import Decimal

from exasol_python_test_framework import udf, docker_db_environment
from exasol_python_test_framework.udf.udf_debug import UdfDebugger, UdfDebuggerFromDockerHost


class UdfDebugTest(udf.TestCase):
    SCHEMA = "UdfDebugTest"

    def _create_vars(self):
        self.create_col_defs = [
            ('C0', 'INT IDENTITY', 'INTEGER'),
            ('C1', 'Decimal(2,0)', 'Decimal(2,0)'),
            ('C2', 'Decimal(4,0)', 'Decimal(4,0)'),
            ('C3', 'Decimal(8,0)', 'Decimal(8,0)'),
            ('C4', 'Decimal(16,0)', 'Decimal(16,0)'),
            ('C5', 'Decimal(36,0)', 'Decimal(36,0)'),
            ('C6', 'DOUBLE', 'DOUBLE'),
            ('C7', 'BOOLEAN', 'BOOLEAN'),
            ('C8', 'VARCHAR(500)', 'VARCHAR(500)'),
            ('C9', 'CHAR(10)', 'CHAR(10)'),
            ('C10', 'DATE', 'DATE'),
            ('C11', 'TIMESTAMP', 'TIMESTAMP')
        ]
        self.create_col_defs_str = ','.join(
            '%s %s' % (name, sql_type_decl)
            for name, sql_type_decl, _
            in self.create_col_defs
        )
        self.col_defs_str = ','.join(
            '%s %s' % (name, udf_type_decl)
            for name, _, udf_type_decl
            in self.create_col_defs
        )
        self.col_names = [name for name, _, _ in self.create_col_defs]
        self.col_names_str = ','.join(self.col_names)
        self.insert_col_names = self.col_names[1:]
        self.insert_col_names_str = ','.join(self.insert_col_names)

        self.col_tuple = (
            Decimal('1'),
            Decimal('1234'),
            Decimal('12345678'),
            Decimal('1234567890123456'),
            Decimal('123456789012345678901234567890123456'),
            12345.6789,
            True,
            'abcdefghij',
            'abcdefgh  ',
            date(2018, 10, 12),
            datetime(2018, 10, 12, 12, 15, 30, 123000)
        )

    def setUp(self):
        self.query(f'CREATE SCHEMA {self.SCHEMA}', ignore_errors=True)
        self.query(f'OPEN SCHEMA {self.SCHEMA}', ignore_errors=True)
        self._create_vars()
        self.create_table_1()

    def create_table(self, table_name, create_col_defs_str):
        create_table_sql = 'CREATE TABLE %s (%s)' % (table_name, create_col_defs_str)
        print("Create Table Statement %s" % create_table_sql)
        self.query(create_table_sql)

    def create_table_1(self):
        self.create_table("TEST1", self.create_col_defs_str)
        print(f"Start initial insert with: {self.insert_col_names_str}", flush=True)
        self.import_via_insert("TEST1", [self.col_tuple], column_names=self.insert_col_names)
        num_inserts = 17  # => 2^17 = ~128 K rows
        for i in range(num_inserts):
            print(f"Start insert iteration {i} with: {self.insert_col_names_str}", flush=True)

            insert_sql = ('INSERT INTO TEST1 (%s) SELECT %s FROM TEST1'
                          % (self.insert_col_names_str, self.insert_col_names_str))
            self.query(insert_sql)
        self.num_rows = 2 ** num_inserts

    @udf.skipIfNot(docker_db_environment.is_available, reason="This test requires a docker-db environment")
    def test_sql_hello_world(self):
        env = docker_db_environment.DockerDBEnvironment(self.SCHEMA)
        self.query('''
            ALTER SESSION SET SCRIPT_LANGUAGES='PYTHON3=localzmq+protobuf:///bfsdefault/default/template-Exasol-all-python-3.10-release-7KUB5GSSRFHFYRIQCYELRMTJXEGVKRSKYWVB6JB47TG74DXF4XKQ?lang=python#buckets/bfsdefault/default/template-Exasol-all-python-3.10-release-7KUB5GSSRFHFYRIQCYELRMTJXEGVKRSKYWVB6JB47TG74DXF4XKQ/exaudf/exaudfclient_py3';
            ''')

        batch_count = 8
        batch_size = self.num_rows / batch_count
        udf_sql = udf.fixindent('''
                    CREATE OR REPLACE PYTHON3 SET SCRIPT
                    foo(%s)
                    EMITS(%s) AS

                    import tracemalloc
                    import gc
                    tracemalloc.start()

                    def process_df(ctx):            
                        df = ctx.get_dataframe(num_rows=%d)
                        ctx.emit(df)

                    def run(ctx):
                        
                        for batch_idx in range(%d):
                            print(f"Processing batch {batch_idx}", flush=True)
                            
                            process_df(ctx)
                            if batch_idx == 0:
                                gc.collect()
                                snapshot_begin = tracemalloc.take_snapshot()
    
                            if batch_idx == (%d - 1):
                                gc.collect()
                                snapshot_end = tracemalloc.take_snapshot()
                                top_stats_begin_end = snapshot_end.compare_to(snapshot_begin, 'lineno')
                                first_item = top_stats_begin_end[0] #First item is always the largest one
                                print(f"Largest memory item is {first_item}", flush=True)
                                if first_item.size_diff > 10000:
                                    raise RuntimeError(f"scalar emit UDF uses too much memory: {first_item}")
                    /
                    ''' % (self.col_defs_str, self.col_defs_str, batch_size, batch_count, batch_count))
        print(udf_sql)
        self.query(udf_sql)

        select_sql = 'SELECT foo(%s) FROM TEST1' % self.col_names_str
        print(select_sql)

        with open("/tmp/out_oom.log", "w") as log_file:
            with UdfDebuggerFromDockerHost(test_case=self, output=log_file):
                rows = self.query(select_sql)
                self.assertEqual(self.num_rows, len(rows))


if __name__ == '__main__':
    udf.main()
