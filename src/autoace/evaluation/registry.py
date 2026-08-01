"""Immutable candidate and experiment registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateDefinition:
    candidate_id: str
    components: tuple[str, ...]
    remote: bool


@dataclass(frozen=True)
class ExperimentDefinition:
    experiment_id: str
    candidate_id: str
    purpose: str


CANDIDATES = tuple(
    CandidateDefinition(candidate, components, remote)
    for candidate, components, remote in (
        ("P0", ("ffmpeg", "dsp", "silero_vad", "rules"), False),
        ("P1", ("P0", "dnsmos", "yamnet", "overlap"), False),
        ("P2", ("P1", "local_emotion"), False),
        ("P3", ("P2", "whisper_tiny_or_base", "local_semantics"), False),
        ("P4", ("gemini_3_5_audio",), True),
        ("P5", ("P4", "P0", "field_fusion"), True),
        ("P6", ("P5", "accepted_local_specialists"), True),
        ("P7", ("P6", "gemini_3_6_text"), True),
        ("P8", ("gemini_3_6_audio_upper_bound",), True),
    )
)

EXPERIMENTS = tuple(
    ExperimentDefinition(experiment_id, candidate_id, purpose)
    for experiment_id, candidate_id, purpose in (
        ("E00", "P0", "deterministic lower bound"),
        ("E01", "P1", "DNSMOS ablation"),
        ("E02", "P1", "YAMNet ablation"),
        ("E03", "P1", "overlap ablation"),
        ("E04", "P1", "accepted local specialist combination"),
        ("E05", "P2", "SpeechBrain emotion challenger"),
        ("E06", "P2", "emotion2vec challenger"),
        ("E07", "P3", "Whisper tiny challenger"),
        ("E08", "P3", "Whisper base challenger"),
        ("E09", "P4", "Gemini 3.5 audio"),
        ("E10", "P5", "Gemini plus deterministic fusion"),
        ("E11", "P6", "Gemini plus accepted specialists"),
        ("E12", "P7", "batched Gemini 3.6 text"),
        ("E13", "P8", "bounded Gemini 3.6 audio upper bound"),
    )
)
