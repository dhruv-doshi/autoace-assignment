from __future__ import annotations

from pathlib import Path

from autoace.inference.observation_cache import ObservationCache


def test_cache_key_and_reuse(tmp_path: Path) -> None:
    cache = ObservationCache(tmp_path)
    key = cache.key("audio-hash", "model", "prompt", "schema", "config")
    cache.put(key, {"file_id": "call.wav", "value": "redacted"})
    cached = cache.get(key)
    assert cached is not None
    assert cached["value"] == "redacted"
    assert cache.stats().hits == 1


def test_cache_does_not_return_missing_key(tmp_path: Path) -> None:
    cache = ObservationCache(tmp_path)
    assert cache.get("missing") is None
