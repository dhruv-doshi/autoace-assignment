"""Candidate comparison and hard-gate reporting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    field_scores: dict[str, float]
    per_minute_cost: float
    peak_rss_mb: float
    gates_passed: bool

    @property
    def average_score(self) -> float:
        return (
            sum(self.field_scores.values()) / len(self.field_scores)
            if self.field_scores
            else 0.0
        )


def select_winner(scores: list[CandidateScore]) -> CandidateScore:
    eligible = [score for score in scores if score.gates_passed]
    if not eligible:
        raise RuntimeError("no eligible candidate satisfies all hard gates")
    return max(eligible, key=lambda score: (score.average_score, -score.per_minute_cost))
