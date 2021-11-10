# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['exasol_python_test_framework',
 'exasol_python_test_framework.docker_db_environment',
 'exasol_python_test_framework.exatest',
 'exasol_python_test_framework.exatest.clients',
 'exasol_python_test_framework.exatest.servers',
 'exasol_python_test_framework.exatest.test',
 'exasol_python_test_framework.performance',
 'exasol_python_test_framework.udf']

package_data = \
{'': ['*']}

install_requires = \
['docker>=5.0.3',
 'numpy>=1.19.5',
 'pyftpdlib>=1.5.6',
 'pyodbc>=4.0.27',
 'scipy>=1.2.1']

setup_kwargs = {
    'name': 'exasol-python-test-framework',
    'version': '0.2.0',
    'description': 'Python Test framework for Exasol database tests',
    'long_description': '# Exasol Python Test Framework\n\n## About\n\nThis project is shared among other Exasol projects, and provides a test framework to execute integration tests on the database. \n\n\n## Prerequisites\n\n* Python3\n\n',
    'author': 'Exasol AG',
    'author_email': 'opensource@exasol.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/exasol/exasol-python-test-framework',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6,<4',
}


setup(**setup_kwargs)
