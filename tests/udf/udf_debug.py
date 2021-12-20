import io

from exasol_python_test_framework import udf
from exasol_python_test_framework.udf.udf_debug import UdfDebugger


class UdfDebugTest(udf.TestCase):
    def setUp(self):
        self.query('CREATE SCHEMA FN2', ignore_errors=True)
        self.query('OPEN SCHEMA FN2', ignore_errors=True)

    def test_sql_hello_world(self):
        self.query(udf.fixindent('''
                CREATE OR REPLACE python3 SCALAR SCRIPT
                print_something()
                RETURNS int AS

                def run(ctx):
                    print("Hello from UDF", flust=True)
                /
                '''))

        output = io.StringIO()
        with UdfDebugger(self, output):
            self.query('SELECT print_something() FROM DUAL')

        self.assertIn("Hello from UDF", output.buffer)


if __name__ == '__main__':
    udf.main()



