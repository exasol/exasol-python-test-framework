from __future__ import annotations

from pathlib import Path
from pydantic import computed_field

from exasol.toolbox.config import BaseConfig


class Config(BaseConfig):
    @computed_field  # type: ignore[misc]
    @property
    def source_code_path(self) -> Path:
        """
        Path to the source code of the project.

        This needs to be overridden due to a custom directory setup. This will be
        addressed in:
            https://github.com/exasol/exasol-python-test-framework/issues/106
        """
        return self.root_path / self.project_name

PROJECT_CONFIG = Config(
    project_name="exasol_python_test_framework",
    root_path=Path(__file__).parent,
)