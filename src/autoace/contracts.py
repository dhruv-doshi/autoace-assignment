"""Typed public and experiment contracts."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Tone = Literal["neutral", "satisfied", "frustrated", "upset", "distressed"]
Intensity = Literal["low", "medium", "high"]
NoiseSeverity = Literal["none", "low", "medium", "high"]
Quality = Literal["clear", "slightly_impaired", "severely_impaired"]
ExperimentId = Literal[
    "E00", "E01", "E02", "E03", "E04", "E05", "E06", "E07",
    "E08", "E09", "E10", "E11", "E12", "E13"
]
CandidateId = Literal["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class CallAnalysisResult(StrictModel):
    emotional_tone: Tone
    emotional_intensity: Intensity
    background_noise_present: bool
    background_noise_type: str
    background_noise_severity: NoiseSeverity
    audio_quality: Quality
    speaker_overlap_present: bool
    long_silence_present: bool
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_noise_invariants(self) -> CallAnalysisResult:
        if not math.isfinite(self.confidence):
            raise ValueError("confidence must be finite")
        if self.background_noise_present:
            if not self.background_noise_type.strip():
                raise ValueError("noise type is required when noise is present")
            if self.background_noise_severity == "none":
                raise ValueError("noise severity cannot be none when noise is present")
        elif self.background_noise_type or self.background_noise_severity != "none":
            raise ValueError("no-noise results require empty type and none severity")
        return self


class EvidenceCandidate(StrictModel):
    emotional_tone: Tone
    emotional_intensity: Intensity
    background_noise_present: bool
    background_noise_type: str
    background_noise_severity: NoiseSeverity
    audio_quality: Quality
    speaker_overlap_present: bool
    long_silence_present: bool


class CustomerRole(StrictModel):
    identified: bool
    certainty: Literal["low", "medium", "high"]


class RemoteEvidence(StrictModel):
    file_id: str = Field(min_length=1)
    customer_role: CustomerRole
    field_candidates: EvidenceCandidate
    evidence: list[dict[str, object]] = Field(default_factory=list, max_length=12)
    ambiguities: list[str] = Field(default_factory=list, max_length=8)


class ExperimentEnvironment(StrictModel):
    python_version: str
    venv_lock_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    ffmpeg_version: str
    platform: str
    cpu: str | None = None


class GateResults(StrictModel):
    contract: bool
    accuracy: bool
    cost: bool
    memory: bool
    privacy: bool
    license: bool
    reproducibility: bool


class ExperimentRun(StrictModel):
    run_id: str = Field(min_length=1)
    experiment_id: ExperimentId
    candidate_id: CandidateId
    candidate_revision: str = Field(pattern=r"^[a-f0-9]{64}$")
    dataset_version: str = Field(min_length=1)
    split: Literal["smoke", "development", "calibration", "holdout"]
    environment: ExperimentEnvironment
    status: Literal[
        "declared", "eligible", "running", "complete", "accepted",
        "rejected", "blocked", "failed"
    ]
    blocked_reasons: list[str] = Field(default_factory=list)
    field_metrics: dict[str, float] = Field(default_factory=dict)
    calibration_metrics: dict[str, float] = Field(default_factory=dict)
    cost: dict[str, float | int] = Field(default_factory=dict)
    performance: dict[str, float] = Field(default_factory=dict)
    gate_results: GateResults
    artifact_hashes: dict[str, str] = Field(default_factory=dict)


class WinningCandidate(StrictModel):
    candidate_id: CandidateId
    revision: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReleaseEnvironment(StrictModel):
    python_version: str
    venv_lock_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    ffmpeg_version: str
    target_memory_mb: Literal[2048]
    platform: str | None = None


class ModelArtifact(StrictModel):
    name: str
    revision: str
    license: str
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    remote: bool = False


class ReleaseManifest(StrictModel):
    release_id: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    winning_candidate: WinningCandidate
    environment: ReleaseEnvironment
    models: list[ModelArtifact]
    configuration_hashes: dict[str, str] = Field(default_factory=dict)
    evaluation_runs: list[str] = Field(min_length=1)
    rejected_candidates: list[dict[str, str]] = Field(default_factory=list)
    gate_results: GateResults
    created_at: datetime

    @model_validator(mode="after")
    def require_all_gates(self) -> ReleaseManifest:
        if not all(self.gate_results.model_dump().values()):
            raise ValueError("release manifest requires all gates to pass")
        return self
