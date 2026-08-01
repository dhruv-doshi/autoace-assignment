from __future__ import annotations

from autoace.contracts import ExperimentRun, ReleaseManifest


def test_experiment_run_accepts_all_declared_ids() -> None:
    run = ExperimentRun.model_validate(
        {
            "run_id": "run-1",
            "experiment_id": "E00",
            "candidate_id": "P0",
            "candidate_revision": "a" * 64,
            "dataset_version": "dev-1",
            "split": "development",
            "environment": {
                "python_version": "3.12.13",
                "venv_lock_sha256": "b" * 64,
                "ffmpeg_version": "ffmpeg",
                "platform": "test",
            },
            "status": "complete",
            "gate_results": {
                "contract": True,
                "accuracy": True,
                "cost": True,
                "memory": True,
                "privacy": True,
                "license": True,
                "reproducibility": True,
            },
        }
    )
    assert run.candidate_id == "P0"


def test_release_manifest_requires_all_true_gates() -> None:
    payload = {
        "release_id": "r1",
        "source_revision": "local",
        "winning_candidate": {"candidate_id": "P0", "revision": "a" * 64},
        "environment": {
            "python_version": "3.12.13",
            "venv_lock_sha256": "b" * 64,
            "ffmpeg_version": "ffmpeg",
            "target_memory_mb": 2048,
        },
        "models": [],
        "configuration_hashes": {},
        "evaluation_runs": ["run-1"],
        "gate_results": {key: True for key in (
            "contract", "accuracy", "cost", "memory", "privacy", "license", "reproducibility"
        )},
        "created_at": "2026-08-01T00:00:00Z",
    }
    assert ReleaseManifest.model_validate(payload).release_id == "r1"
