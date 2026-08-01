from autoace.evaluation.registry import CANDIDATES, EXPERIMENTS


def test_registry_contains_all_candidates_and_experiments() -> None:
    assert {candidate.candidate_id for candidate in CANDIDATES} == {f"P{i}" for i in range(9)}
    assert {experiment.experiment_id for experiment in EXPERIMENTS} == {
        f"E{i:02d}" for i in range(14)
    }
