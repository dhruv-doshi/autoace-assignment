"""Field-specific deterministic baseline fusion."""

from __future__ import annotations

from typing import cast

from autoace.contracts import CallAnalysisResult, NoiseSeverity, Quality


def p0_result(
    *,
    quality: dict[str, object],
    events: dict[str, object],
    vad: dict[str, object],
    overlap: dict[str, object],
) -> CallAnalysisResult:
    noise_present = bool(events.get("background_noise_present", False))
    noise_type = str(events.get("background_noise_type", "")) if noise_present else ""
    severity: NoiseSeverity = cast(
        NoiseSeverity,
        str(events.get("background_noise_severity", "low")) if noise_present else "none",
    )
    quality_value = cast(Quality, str(quality.get("audio_quality", "clear")))
    # A conversational pause can readily reach several seconds; reserve this
    # flag for a genuinely long interruption. Energy VAD is intentionally
    # conservative here because it can split low-volume speech into pauses.
    silence = float(cast(float, vad.get("longest_silence_seconds", 0.0))) >= 8.0
    return CallAnalysisResult(
        emotional_tone="neutral",
        emotional_intensity="low",
        background_noise_present=noise_present,
        background_noise_type=noise_type,
        background_noise_severity=severity,
        audio_quality=quality_value,
        speaker_overlap_present=bool(overlap.get("speaker_overlap_present", False)),
        long_silence_present=silence,
        confidence=0.25,
    )
