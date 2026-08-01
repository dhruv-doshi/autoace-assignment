from pathlib import Path

import pytest

from autoace.inference.gemini_audio import (
    OpenRouterAudioObserver,
    RemoteRouteUnavailable,
)


def test_remote_observer_requires_key_before_provider_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    observer = OpenRouterAudioObserver(api_key=None)
    with pytest.raises(RemoteRouteUnavailable, match="not configured"):
        observer.observe(tmp_path / "missing.wav", audio_seconds=60)
