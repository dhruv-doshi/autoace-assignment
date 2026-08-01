from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from autoace.contracts import CallAnalysisResult


def valid_result() -> dict[str, object]:
    return {
        "emotional_tone": "neutral",
        "emotional_intensity": "medium",
        "background_noise_present": False,
        "background_noise_type": "",
        "background_noise_severity": "none",
        "audio_quality": "clear",
        "speaker_overlap_present": False,
        "long_silence_present": False,
        "confidence": 0.82,
    }


def test_valid_result_round_trips_exactly() -> None:
    result = CallAnalysisResult.model_validate(valid_result())
    assert set(result.model_dump()) == set(valid_result())


@pytest.mark.parametrize(
    ("field", "value"),
    [("emotional_tone", "angry"), ("emotional_intensity", "severe"), ("audio_quality", "bad")],
)
def test_invalid_enums_are_rejected(field: str, value: str) -> None:
    payload = valid_result()
    payload[field] = value
    with pytest.raises(ValidationError):
        CallAnalysisResult.model_validate(payload)


def test_noise_invariants_are_rejected() -> None:
    payload = valid_result()
    payload["background_noise_type"] = "television"
    with pytest.raises(ValidationError):
        CallAnalysisResult.model_validate(payload)

    payload = valid_result()
    payload["background_noise_present"] = True
    with pytest.raises(ValidationError):
        CallAnalysisResult.model_validate(payload)


def test_confidence_must_be_finite_and_bounded() -> None:
    for value in (-0.01, 1.01, math.inf, math.nan):
        payload = valid_result()
        payload["confidence"] = value
        with pytest.raises(ValidationError):
            CallAnalysisResult.model_validate(payload)
