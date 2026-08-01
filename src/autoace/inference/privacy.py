"""Local-only helpers for remote inference privacy and lifecycle checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_PATH_RE = re.compile(r"(?<![\w/])(?:/[\w.-]+)+")
_TOKEN_RE = re.compile(r"(?i)(api[_ -]?key|token|secret|authorization)(\s*[:=]\s*)[^,;\s]+")


def redact_error(message: str) -> str:
    """Remove likely credentials and absolute local paths from user-facing errors."""
    redacted = _TOKEN_RE.sub(r"\1\2[REDACTED]", message)
    return _PATH_RE.sub("[PATH]", redacted)


@dataclass
class RemoteFileLedger:
    """Tracks temporary files that must be deleted before a remote call returns."""

    paths: list[Path] = field(default_factory=list)

    def register(self, path: Path) -> None:
        self.paths.append(path)

    def cleanup(self) -> list[str]:
        failures: list[str] = []
        for path in self.paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                failures.append(str(path))
        self.paths.clear()
        return failures

    def __enter__(self) -> RemoteFileLedger:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        failures = self.cleanup()
        if failures and exc is None:
            raise RuntimeError("remote temporary-file cleanup failed")
