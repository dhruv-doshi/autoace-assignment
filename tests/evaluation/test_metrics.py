from __future__ import annotations

from autoace.evaluation.metrics import balanced_accuracy, macro_f1


def test_classification_metrics_are_bounded() -> None:
    truth = ["a", "a", "b", "b"]
    prediction = ["a", "b", "b", "b"]
    assert 0 < macro_f1(truth, prediction) < 1
    assert 0 < balanced_accuracy(truth, prediction) < 1
