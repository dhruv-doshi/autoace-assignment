"""Channel-layout evidence and optional overlap model boundary."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def channel_layout_evidence(
    channels: np.ndarray, *, channel_correlation: float | None
) -> dict[str, object]:
    values = np.asarray(channels)
    independent_stereo = (
        values.ndim == 2 and values.shape[1] == 2 and channel_correlation is not None
        and abs(channel_correlation) < 0.98
    )
    dual_mono = values.ndim == 2 and values.shape[1] == 2 and not independent_stereo
    return {
        "dual_mono": dual_mono,
        "independent_stereo": independent_stereo,
        "speaker_overlap_present": False,
        "backend": "channel_layout_only",
        "requires_model_for_mono": not independent_stereo,
    }


def spectral_overlap_proxy(
    samples: np.ndarray, sample_rate_hz: int
) -> dict[str, object]:
    """Detect likely concurrent voiced sources from low-frequency polyphony.

    This inexpensive proxy looks for two or more strong local spectral peaks in
    the human-voice fundamental range during speech-level frames. It cannot
    replace a diarization/overlap model, but unlike channel-layout inspection it
    remains informative for dual-mono recordings.
    """

    values = np.asarray(samples, dtype=np.float32)
    mono = values.mean(axis=1) if values.ndim == 2 else values.reshape(-1)
    frame_size = max(64, int(sample_rate_hz * 0.04))
    hop = max(1, frame_size // 2)
    low_bin = max(1, int(70 * frame_size / sample_rate_hz))
    high_bin = min(frame_size // 2, int(500 * frame_size / sample_rate_hz))
    peak_counts: list[int] = []
    window = np.hanning(frame_size).astype(np.float32)
    for start in range(0, max(0, mono.size - frame_size + 1), hop):
        frame = mono[start:start + frame_size] * window
        if float(np.sqrt(np.mean(frame * frame))) < 0.015:
            continue
        band = np.abs(np.fft.rfft(frame))[low_bin:high_bin]
        if band.size < 3 or float(np.max(band)) == 0.0:
            continue
        peaks = (band[1:-1] > band[:-2]) & (band[1:-1] > band[2:])
        strong = band[1:-1] > float(np.max(band)) * 0.20
        peak_counts.append(int(np.sum(peaks & strong)))
    median_peak_count = float(np.median(peak_counts)) if peak_counts else 0.0
    return {
        "speaker_overlap_present": median_peak_count >= 2.0,
        "backend": "spectral_polyphony_proxy",
        "speech_level_frame_count": len(peak_counts),
        "median_voice_peak_count": median_peak_count,
        "note": "Heuristic only; validate against a labeled overlap set before production use.",
    }


class OverlapModel:
    """Placeholder boundary for an admitted pyannote/ONNX overlap model."""

    def __init__(self, model_path: Path) -> None:
        if not model_path.is_file():
            raise RuntimeError(f"overlap artifact unavailable: {model_path}")

    def predict(self, _samples: object, _sample_rate_hz: int) -> dict[str, object]:
        raise NotImplementedError("overlap model adapter requires a validated artifact")
