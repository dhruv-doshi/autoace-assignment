"""Transparent acoustic-event evidence used by production P6."""

from __future__ import annotations


def acoustic_event_proxy(features: dict[str, float]) -> dict[str, object]:
    """Classify a small, explicit set of persistent-noise signatures.

    This is deliberately a conservative DSP calibration, not a substitute for
    an audio-event model.  The feature combinations correspond to broad
    spectral families: flat/high-bandwidth noise and low-level, highly dynamic
    programme-like audio.  Keeping the decision boundaries here makes their
    limitations visible in the run statistics.
    """

    flatness = features.get("spectral_flatness", 0.0)
    zcr = features.get("zcr", 0.0)
    bandwidth_hz = features.get("bandwidth_hz", 0.0)
    crest_factor = features.get("crest_factor", 0.0)
    dbfs = features.get("dbfs", -120.0)
    if flatness >= 0.28 and bandwidth_hz >= 1_300:
        present, noise_type, severity, reason = (
            True,
            "sharp static",
            "medium",
            "flat, wide-band non-speech energy",
        )
    elif crest_factor >= 12.0 and dbfs <= -24.0:
        present, noise_type, severity, reason = (
            True,
            "TV",
            "medium",
            "low-level programme-like dynamic range",
        )
    elif flatness > 0.75 or zcr > 0.30:
        present, noise_type, severity, reason = (
            True,
            "broadband static",
            "low",
            "very flat or high zero-crossing background",
        )
    else:
        present, noise_type, severity, reason = False, "", "none", "no persistent signature"
    return {
        "background_noise_present": present,
        "background_noise_type": noise_type,
        "background_noise_severity": severity,
        "backend": "dsp_proxy",
        "yamnet": None,
        "reason": reason,
    }
