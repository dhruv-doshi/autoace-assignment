from __future__ import annotations

import numpy as np

from autoace.audio.events import acoustic_event_proxy
from autoace.audio.overlap import channel_layout_evidence, spectral_overlap_proxy
from autoace.audio.quality import quality_proxy


def test_quality_proxy_separates_clean_signal_from_clipping() -> None:
    clean = quality_proxy({"clipping_ratio": 0.0, "dbfs": -18.0, "spectral_flatness": 0.1})
    clipped = quality_proxy({"clipping_ratio": 0.05, "dbfs": -2.0, "spectral_flatness": 0.8})
    assert clean["audio_quality"] == "clear"
    assert clipped["audio_quality"] == "severely_impaired"


def test_event_proxy_is_explicitly_heuristic() -> None:
    result = acoustic_event_proxy({"spectral_flatness": 0.9, "zcr": 0.4})
    assert result["backend"] == "dsp_proxy"
    assert result["background_noise_present"] is True


def test_event_proxy_distinguishes_calibrated_noise_signatures() -> None:
    television = acoustic_event_proxy(
        {"spectral_flatness": 0.18, "bandwidth_hz": 1_100, "crest_factor": 13.0, "dbfs": -27.0}
    )
    static = acoustic_event_proxy(
        {"spectral_flatness": 0.34, "bandwidth_hz": 1_500, "crest_factor": 8.0, "dbfs": -19.0}
    )
    assert (
        television["background_noise_type"],
        television["background_noise_severity"],
    ) == ("TV", "medium")
    assert (
        static["background_noise_type"],
        static["background_noise_severity"],
    ) == ("sharp static", "medium")


def test_dual_mono_does_not_trigger_overlap() -> None:
    left = np.ones(16000, dtype=np.float32)
    stereo = np.column_stack([left, left])
    evidence = channel_layout_evidence(stereo, channel_correlation=1.0)
    assert evidence["dual_mono"] is True
    assert evidence["speaker_overlap_present"] is False


def test_spectral_overlap_proxy_detects_two_voice_peaks() -> None:
    seconds = 1
    time = np.arange(16_000 * seconds, dtype=np.float32) / 16_000
    one_voice = 0.1 * np.sin(2 * np.pi * 140 * time)
    two_voices = one_voice + 0.08 * np.sin(2 * np.pi * 230 * time)
    assert spectral_overlap_proxy(one_voice, 16_000)["speaker_overlap_present"] is False
    assert spectral_overlap_proxy(two_voices, 16_000)["speaker_overlap_present"] is True
