from __future__ import annotations

from pathlib import Path

from exasol.toolbox.config import BaseConfig

PROJECT_CONFIG = BaseConfig(
    project_name="exasol_python_test_framework",
    root_path=Path(__file__).parent,
)