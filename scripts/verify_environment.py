"""Verify the reproducible Python/native execution environment."""

from __future__ import annotations

import pathlib
import platform
import shutil
import sys


def main() -> int:
    executable = pathlib.Path(sys.executable).resolve()
    if ".venv" not in executable.parts:
        print(f"ERROR: Python executable is outside .venv: {executable}")
        return 1
    if sys.version_info[:2] != (3, 12):
        print(f"ERROR: Python 3.12 required, found {platform.python_version()}")
        return 1
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    print(f"python={executable}")
    print(f"python_version={platform.python_version()}")
    print(f"platform={platform.platform()}")
    print(f"ffmpeg={ffmpeg or 'missing'}")
    print(f"ffprobe={ffprobe or 'missing'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
