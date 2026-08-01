from __future__ import annotations

import numpy as np

from autoace.audio.vad import SileroVad, energy_vad

ROOT = __import__("pathlib").Path(__file__).parents[2]


def test_energy_vad_finds_internal_silence() -> None:
    rng = np.random.default_rng(3)
    signal = np.concatenate(
        [rng.normal(0, 0.1, 16000), np.zeros(16000), rng.normal(0, 0.1, 16000)]
    ).astype(np.float32)
    result = energy_vad(signal, 16000)
    assert result.speech_ratio > 0.3
    assert result.longest_silence_seconds > 0.5
    assert len(result.segments) >= 2


def test_silero_onnx_runs_on_cpu_fixture() -> None:
    signal = np.zeros(16000, dtype=np.float32)
    result = SileroVad(ROOT / "models" / "silero_vad.onnx").run(signal, 16000)
    assert result.backend == "silero_onnx"
    assert 0.0 <= result.speech_ratio <= 1.0
