from __future__ import annotations

import numpy as np

from autoace.audio.dsp import summarize_audio


def test_dsp_detects_clipping_and_nonzero_signal() -> None:
    samples = np.zeros(16000, dtype=np.float32)
    samples[::100] = 1.0
    summary = summarize_audio(samples, 16000)
    assert summary["peak_abs"] == 1.0
    assert summary["clipping_ratio"] > 0
    assert summary["rms"] > 0


def test_dsp_silence_has_near_zero_energy() -> None:
    summary = summarize_audio(np.zeros(16000, dtype=np.float32), 16000)
    assert summary["rms"] == 0.0
    assert summary["zcr"] == 0.0
