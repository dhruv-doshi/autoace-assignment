"""Record a blocked experiment without inventing metrics or provider results."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import cast

from autoace.contracts import CandidateId, ExperimentEnvironment, ExperimentRun, GateResults
from autoace.environment import capture_environment
from autoace.evaluation.experiments import write_experiment
from autoace.evaluation.registry import EXPERIMENTS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--experiment",
        required=True,
        choices=[item.experiment_id for item in EXPERIMENTS],
    )
    parser.add_argument("--reason", action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/experiments"))
    args = parser.parse_args()
    definition = next(item for item in EXPERIMENTS if item.experiment_id == args.experiment)
    captured = capture_environment(Path("uv.lock"))
    environment = ExperimentEnvironment(
        python_version=str(captured["python_version"] or "unknown"),
        venv_lock_sha256=str(captured["venv_lock_sha256"] or "0" * 64),
        ffmpeg_version=str(captured["ffmpeg_version"] or "missing"),
        platform=str(captured["platform"] or "unknown"),
        cpu=str(captured["cpu"] or "unknown"),
    )
    run = ExperimentRun(
        run_id=f"{args.experiment.lower()}-blocked",
        experiment_id=args.experiment,
        candidate_id=cast(CandidateId, definition.candidate_id),
        candidate_revision=hashlib.sha256(definition.candidate_id.encode()).hexdigest(),
        dataset_version="not-run",
        split="development",
        environment=environment,
        status="blocked",
        blocked_reasons=args.reason,
        gate_results=GateResults(
            contract=True, accuracy=False, cost=False, memory=False,
            privacy=False, license=False, reproducibility=True,
        ),
    )
    try:
        artifact = write_experiment(run, args.output_dir)
    except FileExistsError:
        artifact = args.output_dir / f"{run.run_id}.json"
    print(f"artifact={artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
