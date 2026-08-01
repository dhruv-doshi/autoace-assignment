from __future__ import annotations

import numpy as np

from autoace.audio.vad import energy_vad


def test_energy_vad_finds_internal_silence() -> None:
    rng = np.random.default_rng(3)
    signal = np.concatenate(
        [rng.normal(0, 0.1, 16000), np.zeros(16000), rng.normal(0, 0.1, 16000)]
    ).astype(np.float32)
    result = energy_vad(signal, 16000)
    assert result.speech_ratio > 0.3
    assert result.longest_silence_seconds > 0.5
    assert len(result.segments) >= 2
