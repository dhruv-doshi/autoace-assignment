"""Deterministic quality evidence used by production P6."""

from __future__ import annotations


def quality_proxy(features: dict[str, float]) -> dict[str, object]:
    clipping = features.get("clipping_ratio", 0.0)
    level = features.get("dbfs", -100.0)
    flatness = features.get("spectral_flatness", 0.0)
    if clipping >= 0.01 or level > -1.0:
        quality = "severely_impaired"
    elif clipping >= 0.001 or level < -45.0 or flatness > 0.9:
        quality = "slightly_impaired"
    else:
        quality = "clear"
    return {
        "audio_quality": quality,
        "backend": "dsp_proxy",
        "reason": "transparent clipping, level, and spectral thresholds",
    }
