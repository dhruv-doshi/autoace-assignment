"""Deterministic, interpretable signal evidence."""

from __future__ import annotations

import numpy as np


def summarize_audio(samples: np.ndarray, sample_rate_hz: int) -> dict[str, float]:
    values = np.asarray(samples, dtype=np.float32).reshape(-1)
    if values.size == 0:
        raise ValueError("audio cannot be empty")
    rms = float(np.sqrt(np.mean(values * values)))
    peak = float(np.max(np.abs(values)))
    zcr = (
        float(np.mean(np.signbit(values[:-1]) != np.signbit(values[1:])))
        if values.size > 1
        else 0.0
    )
    spectrum = np.abs(np.fft.rfft(values - np.mean(values)))
    frequencies = np.fft.rfftfreq(values.size, 1 / sample_rate_hz)
    spectral_total = float(np.sum(spectrum))
    centroid = float(np.sum(frequencies * spectrum) / spectral_total) if spectral_total else 0.0
    geometric = float(np.exp(np.mean(np.log(spectrum + 1e-12))))
    arithmetic = float(np.mean(spectrum))
    return {
        "duration_seconds": values.size / sample_rate_hz,
        "rms": rms,
        "dbfs": float(20 * np.log10(max(rms, 1e-12))),
        "peak_abs": peak,
        "clipping_ratio": float(np.mean(np.abs(values) >= 0.999)),
        "dc_offset": float(np.mean(values)),
        "crest_factor": float(peak / rms) if rms else 0.0,
        "zcr": zcr,
        "spectral_centroid_hz": centroid,
        "spectral_flatness": geometric / arithmetic if arithmetic else 0.0,
        "bandwidth_hz": float(
            np.sqrt(np.sum(((frequencies - centroid) ** 2) * spectrum) / spectral_total)
        )
        if spectral_total else 0.0,
    }


def channel_correlation(channels: np.ndarray) -> float | None:
    values = np.asarray(channels, dtype=np.float32)
    if values.ndim != 2 or values.shape[1] != 2:
        return None
    left, right = values[:, 0], values[:, 1]
    if np.std(left) == 0 or np.std(right) == 0:
        return 1.0 if np.allclose(left, right) else 0.0
    return float(np.corrcoef(left, right)[0, 1])
