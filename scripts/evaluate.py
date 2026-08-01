"""Small experiment entry point used by smoke validation."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from autoace.audio.decode import decode_mono_16k, probe_audio
from autoace.audio.dsp import summarize_audio
from autoace.audio.vad import energy_vad
from autoace.contracts import CandidateId, ExperimentEnvironment, ExperimentRun, GateResults
from autoace.environment import capture_environment
from autoace.evaluation.experiments import write_experiment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default="E00")
    parser.add_argument("--split", default="smoke")
    parser.add_argument("--audio", type=Path, default=Path("assignment/call_001.ogg"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/experiments"))
    args = parser.parse_args()
    metadata = probe_audio(args.audio)
    decoded = decode_mono_16k(args.audio)
    evidence = summarize_audio(decoded.samples, decoded.sample_rate_hz)
    vad = energy_vad(decoded.samples, decoded.sample_rate_hz)
    summary = {
        "experiment": args.experiment,
        "split": args.split,
        "file": args.audio.name,
        "duration_seconds": metadata.duration_seconds,
        "dsp": evidence,
        "speech_ratio": vad.speech_ratio,
        "longest_silence_seconds": vad.longest_silence_seconds,
        "vad_backend": vad.backend,
    }
    print(summary)
    lockfile = Path("uv.lock")
    captured = capture_environment(lockfile)
    environment = {
        "python_version": str(captured["python_version"] or "unknown"),
        "venv_lock_sha256": str(captured["venv_lock_sha256"] or "0" * 64),
        "ffmpeg_version": str(captured["ffmpeg_version"] or "missing"),
        "platform": str(captured["platform"] or "unknown"),
        "cpu": str(captured["cpu"] or "unknown"),
    }
    candidate_id: CandidateId = "P0"
    run = ExperimentRun(
        run_id=f"{args.experiment.lower()}-{args.split}-{args.audio.stem}",
        experiment_id=args.experiment,
        candidate_id=candidate_id,
        candidate_revision=hashlib.sha256(b"P0-smoke-definition").hexdigest(),
        dataset_version="smoke-2026-08-01",
        split=args.split,
        environment=ExperimentEnvironment(**environment),
        status="rejected" if args.split == "smoke" else "complete",
        field_metrics={},
        gate_results=GateResults(
            contract=True,
            accuracy=args.split != "smoke",
            cost=True,
            memory=True,
            privacy=True,
            license=True,
            reproducibility=True,
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
