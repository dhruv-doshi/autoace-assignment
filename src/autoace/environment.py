"""Version and host information used in experiment/release manifests."""

from __future__ import annotations

import hashlib
import os
import pathlib
import platform
import shutil
import subprocess
import sys


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_version(command: str) -> str | None:
    executable = shutil.which(command)
    if executable is None:
        return None
    result = subprocess.run(
        [executable, "-version"], capture_output=True, text=True, check=False
    )
    first_line = (result.stdout or result.stderr).splitlines()
    return first_line[0] if first_line else None


def capture_environment(lockfile: pathlib.Path | None = None) -> dict[str, str | None]:
    lock_hash = sha256_file(lockfile) if lockfile and lockfile.exists() else None
    return {
        "python_version": platform.python_version(),
        "python_executable": str(pathlib.Path(sys.executable).resolve()),
        "venv_prefix": os.environ.get("VIRTUAL_ENV"),
        "venv_lock_sha256": lock_hash,
        "platform": platform.platform(),
        "cpu": platform.processor(),
        "ffmpeg_version": command_version("ffmpeg"),
        "ffprobe_version": command_version("ffprobe"),
    }
