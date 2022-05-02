import io

from exasol_python_test_framework import udf, docker_db_environment
from exasol_python_test_framework.udf.available_python_packages_utils import run_python_package_import_test


class AvailablePackageTest(udf.TestCase):
    SCHEMA = "AvailablePackageTest"

    def setUp(self):
        self.query(f'CREATE SCHEMA {self.SCHEMA}', ignore_errors=True)
        self.query(f'OPEN SCHEMA {self.SCHEMA}', ignore_errors=True)

    def test_package_available(self):
        run_python_package_import_test(self, "pandas", "PYTHON3", fail=False, alternative=None)

    def test_package_not_available(self):
        run_python_package_import_test(self, "asdgkdbalgf", "PYTHON3", fail=True, alternative=None)

    def test_package_not_available_alternative(self):
        run_python_package_import_test(self, "asdgkdbalgf", "PYTHON3", fail=False, alternative="pandas")

if __name__ == '__main__':
    udf.main()



