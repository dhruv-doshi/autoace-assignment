from __future__ import annotations

from pathlib import Path

from autoace.audio.decode import decode_mono_16k, probe_audio, sha256_audio

ROOT = Path(__file__).parents[2]


def test_probe_and_hash_assignment_audio() -> None:
    path = ROOT / "assignment" / "call_001.ogg"
    metadata = probe_audio(path)
    assert metadata.duration_seconds > 30
    assert metadata.sample_rate_hz == 48000
    assert metadata.channels == 2
    assert len(sha256_audio(path)) == 64


def test_decode_derivative_is_mono_16khz() -> None:
    audio = decode_mono_16k(ROOT / "assignment" / "call_001.ogg")
    assert audio.sample_rate_hz == 16000
    assert audio.samples.ndim == 1
    assert audio.samples.size > 16000
    assert audio.provenance["purpose"] == "speech_analysis"
