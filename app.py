"""Application entry point."""

from __future__ import annotations

import os
from pathlib import Path


def _load_local_env() -> None:
    """Load simple KEY=VALUE settings from the project-local .env file."""
    env_path = Path(__file__).with_name(".env")
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


_load_local_env()

if __name__ == "__main__":
    from autoace.ui.dashboard import run

    run()
