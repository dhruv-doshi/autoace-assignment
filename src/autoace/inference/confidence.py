"""Conservative confidence helpers; calibration remains data-dependent."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceEstimate:
    value: float
    calibrated: bool
    reason: str


def provisional_confidence(
    *,
    base: float,
    agreement: float,
    role_certainty: float,
    quality: float,
) -> ConfidenceEstimate:
    value = max(0.0, min(1.0, base * agreement * role_certainty * quality))
    return ConfidenceEstimate(value, False, "representative calibration artifact unavailable")
