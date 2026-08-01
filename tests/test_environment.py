from __future__ import annotations

import pathlib
import sys


def test_tests_run_from_project_venv() -> None:
    executable = pathlib.Path(sys.executable).resolve()
    assert ".venv" in executable.parts
    assert sys.version_info[:2] == (3, 12)
