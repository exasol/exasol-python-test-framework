from exasol_python_test_framework import udf, environment_info
from exasol_python_test_framework import docker_db_environment
from exasol_python_test_framework.exatest import ODBCClient


class EnvironmentInfoTest(udf.TestCase):

    @udf.skipIfNot(docker_db_environment.is_available, reason="This test requires a docker-db environment")
    def test_environment_info_connect_to_db(self):
        schema = "test_connect_from_udf_to_other_container"
        env = docker_db_environment.DockerDBEnvironment(schema)
        env_info = environment_info.from_environment_info_file()
        db_port = env_info.database_info.ports.database
        db_ip = env_info.database_info.container_info.ip_address
        db_container = env.get_docker_db_container()
        assert env.get_ip_address_of_container(db_container) == db_ip

        client = ODBCClient(f"{db_ip}:{db_port}", self.user, self.password)
        client.query(udf.fixindent("SELECT 1 FROM DUAL"))


if __name__ == '__main__':
    udf.main()
