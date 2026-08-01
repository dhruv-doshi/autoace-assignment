from __future__ import annotations

from pathlib import Path
from typing import cast

from autoace.pipeline import (
    analyze_p0,
    analyze_p0_with_stats,
    analyze_p1_with_stats,
    analyze_p2_with_stats,
    analyze_p3_with_stats,
)


def test_p0_pipeline_returns_exact_public_result() -> None:
    result = analyze_p0(Path("assignment/call_001.ogg"))
    assert set(result.model_dump()) == {
        "emotional_tone",
        "emotional_intensity",
        "background_noise_present",
        "background_noise_type",
        "background_noise_severity",
        "audio_quality",
        "speaker_overlap_present",
        "long_silence_present",
        "confidence",
    }


def test_local_candidate_pipelines_return_stats() -> None:
    path = Path("assignment/call_001.ogg")
    for candidate, analyze in (
        ("P1", analyze_p1_with_stats),
        ("P2", analyze_p2_with_stats),
        ("P3", analyze_p3_with_stats),
    ):
        result, stats = analyze(path)
        assert result.audio_quality == "clear"
        assert stats["pipeline"] == candidate

    _result, p3_stats = analyze_p3_with_stats(path)
    transcript = cast(dict[str, object], p3_stats["transcript"])
    assert transcript["backend"] == "faster_whisper_cpu_int8"
    assert result.background_noise_type == ""


def test_local_pipelines_capture_calibrated_audio_evidence() -> None:
    p0, _p0_stats = analyze_p0_with_stats(Path("assignment/call_002.ogg"))
    p2, _p2_stats = analyze_p2_with_stats(Path("assignment/call_001.ogg"))
    p3, _p3_stats = analyze_p3_with_stats(Path("assignment/call_003.ogg"))
    assert (p0.background_noise_present, p0.background_noise_type) == (True, "TV")
    assert p2.emotional_intensity == "high"
    assert (p3.emotional_tone, p3.emotional_intensity) == ("satisfied", "medium")
