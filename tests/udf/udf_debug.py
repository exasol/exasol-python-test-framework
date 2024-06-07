import io

from exasol_python_test_framework import udf, docker_db_environment
from exasol_python_test_framework.udf.udf_debug import UdfDebugger, UdfDebuggerFromDockerHost


class UdfDebugTest(udf.TestCase):
    SCHEMA = "UdfDebugTest"

    def setUp(self):
        self.query(f'CREATE SCHEMA {self.SCHEMA}', ignore_errors=True)
        self.query(f'OPEN SCHEMA {self.SCHEMA}', ignore_errors=True)

    @udf.skipIfNot(docker_db_environment.is_available, reason="This test requires a docker-db environment")
    def test_sql_hello_world(self):
        env = docker_db_environment.DockerDBEnvironment(self.SCHEMA)
        self.query(udf.fixindent('''
                CREATE OR REPLACE python3 SCALAR SCRIPT
                print_something()
                RETURNS int AS

                def run(ctx):
                    print("Hello from UDF", flush=True)
                /
                '''))
        output = io.StringIO()
        with UdfDebuggerFromDockerHost(test_case=self, output=output):
            self.query('SELECT print_something() FROM DUAL')

        self.assertIn("Hello from UDF", output.getvalue())


if __name__ == '__main__':
    udf.main()
