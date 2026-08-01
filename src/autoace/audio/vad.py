"""Speech-activity evidence with a deterministic fallback."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SpeechSegment:
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True)
class VadResult:
    segments: list[SpeechSegment]
    speech_ratio: float
    longest_silence_seconds: float
    backend: str


def energy_vad(
    samples: np.ndarray,
    sample_rate_hz: int,
    *,
    frame_ms: int = 30,
    hop_ms: int = 10,
    threshold_db: float = -42.0,
) -> VadResult:
    values = np.asarray(samples, dtype=np.float32).reshape(-1)
    frame_size = max(1, int(sample_rate_hz * frame_ms / 1000))
    hop = max(1, int(sample_rate_hz * hop_ms / 1000))
    energies: list[float] = []
    starts: list[int] = []
    for start in range(0, max(1, values.size - frame_size + 1), hop):
        frame = values[start:start + frame_size]
        if frame.size < frame_size // 2:
            break
        energies.append(float(20 * np.log10(max(np.sqrt(np.mean(frame * frame)), 1e-12))))
        starts.append(start)
    active = np.asarray(energies) >= threshold_db
    segments: list[SpeechSegment] = []
    segment_start: int | None = None
    for index, is_active in enumerate(active):
        if is_active and segment_start is None:
            segment_start = starts[index]
        if segment_start is not None and (not is_active or index == len(active) - 1):
            end_index = index if not is_active else index + 1
            end_sample = starts[end_index] if end_index < len(starts) else values.size
            segments.append(
                SpeechSegment(segment_start / sample_rate_hz, end_sample / sample_rate_hz)
            )
            segment_start = None
    speech_samples = sum(
        max(0.0, segment.end_seconds - segment.start_seconds) for segment in segments
    )
    duration = values.size / sample_rate_hz
    longest = 0.0
    previous = 0.0
    for segment in segments:
        longest = max(longest, segment.start_seconds - previous)
        previous = segment.end_seconds
    longest = max(longest, duration - previous)
    return VadResult(segments, speech_samples / duration if duration else 0.0, longest, "energy")
