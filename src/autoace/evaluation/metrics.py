"""Small dependency-light classification and calibration metrics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence


def macro_f1(truth: Sequence[str], prediction: Sequence[str]) -> float:
    labels = sorted(set(truth) | set(prediction))
    scores: list[float] = []
    for label in labels:
        pairs = zip(truth, prediction, strict=True)
        tp = sum(actual == label and predicted == label for actual, predicted in pairs)
        pairs = zip(truth, prediction, strict=True)
        fp = sum(actual != label and predicted == label for actual, predicted in pairs)
        pairs = zip(truth, prediction, strict=True)
        fn = sum(actual == label and predicted != label for actual, predicted in pairs)
        denominator = 2 * tp + fp + fn
        scores.append((2 * tp / denominator) if denominator else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def balanced_accuracy(truth: Sequence[str], prediction: Sequence[str]) -> float:
    labels = sorted(set(truth))
    recalls = []
    for label in labels:
        positives = sum(actual == label for actual in truth)
        correct = sum(
            actual == label and predicted == label
            for actual, predicted in zip(truth, prediction, strict=True)
        )
        recalls.append(correct / positives if positives else 0.0)
    return sum(recalls) / len(recalls) if recalls else 0.0


def brier_score(probabilities: Sequence[float], correctness: Sequence[bool]) -> float:
    if len(probabilities) != len(correctness):
        raise ValueError("probabilities and correctness must have equal length")
    if not probabilities:
        return 0.0
    return sum(
        (p - float(correct)) ** 2
        for p, correct in zip(probabilities, correctness, strict=True)
    ) / len(probabilities)


def expected_calibration_error(
    probabilities: Sequence[float], correctness: Sequence[bool], bins: int = 10
) -> float:
    if len(probabilities) != len(correctness):
        raise ValueError("probabilities and correctness must have equal length")
    if not probabilities:
        return 0.0
    buckets: dict[int, list[tuple[float, bool]]] = defaultdict(list)
    for probability, correct in zip(probabilities, correctness, strict=True):
        index = min(bins - 1, max(0, int(probability * bins)))
        buckets[index].append((probability, correct))
    total = len(probabilities)
    return sum(
        len(values) / total
        * abs(sum(probability for probability, _ in values) / len(values)
              - sum(float(correct) for _, correct in values) / len(values))
        for values in buckets.values()
    )
