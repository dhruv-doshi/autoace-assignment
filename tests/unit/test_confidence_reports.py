from __future__ import annotations

import pytest

from autoace.evaluation.reports import CandidateScore, select_winner
from autoace.inference.confidence import provisional_confidence


def test_provisional_confidence_is_not_claimed_calibrated() -> None:
    result = provisional_confidence(base=0.8, agreement=0.9, role_certainty=0.8, quality=0.7)
    assert 0 <= result.value <= 1
    assert result.calibrated is False


def test_winner_requires_hard_gates() -> None:
    with pytest.raises(RuntimeError, match="no eligible"):
        select_winner([CandidateScore("P0", {"tone": 1.0}, 0.0, 70.0, False)])
    winner = select_winner([
        CandidateScore("P0", {"tone": 0.7}, 0.0, 70.0, True),
        CandidateScore("P1", {"tone": 0.8}, 0.001, 120.0, True),
    ])
    assert winner.candidate_id == "P1"
