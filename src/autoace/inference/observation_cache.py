"""Content-addressed cache for immutable structured remote observations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


@dataclass(frozen=True)
class CacheStats:
    hits: int
    misses: int


class ObservationCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._hits = 0
        self._misses = 0

    @staticmethod
    def key(*parts: str) -> str:
        digest = hashlib.sha256()
        for part in parts:
            digest.update(part.encode())
            digest.update(b"\0")
        return digest.hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        path = self.root / f"{key}.json"
        if not path.is_file():
            self._misses += 1
            return None
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            self._misses += 1
            return None
        self._hits += 1
        return cast(dict[str, Any], payload)

    def put(self, key: str, payload: dict[str, Any]) -> None:
        path = self.root / f"{key}.json"
        if path.exists():
            return
        path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")

    def stats(self) -> CacheStats:
        return CacheStats(self._hits, self._misses)
